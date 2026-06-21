import sqlite3
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

from config import DB_PATH

# Memory categories
SEMANTIC   = "semantic"    # facts, conventions, architecture knowledge
EPISODIC   = "episodic"    # past sessions, bug fixes, what was tried
PROCEDURAL = "procedural"  # rules the agent must always follow

VALID_CATEGORIES = {SEMANTIC, EPISODIC, PROCEDURAL}

# Memory sources
SOURCE_SEED    = "seed"     # loaded by scripts/seed_memory.py
SOURCE_SESSION = "session"  # learned during a coding session
SOURCE_FILE    = "file"     # extracted from a Barge source file

VALID_SOURCES = {SOURCE_SEED, SOURCE_SESSION, SOURCE_FILE}

_APPEND_SEPARATOR = "\n---\n"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY,
    category   TEXT    NOT NULL,
    key        TEXT    NOT NULL UNIQUE,
    content    TEXT    NOT NULL,
    source     TEXT    NOT NULL DEFAULT 'seed',
    importance INTEGER NOT NULL DEFAULT 3,
    created_at INTEGER DEFAULT (unixepoch())
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    key,
    content=memories,
    content_rowid=id
);

CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
    INSERT INTO memories_fts(rowid, content, key)
    VALUES (new.id, new.content, new.key);
END;

CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, key)
    VALUES ('delete', old.id, old.content, old.key);
END;

CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
    INSERT INTO memories_fts(memories_fts, rowid, content, key)
    VALUES ('delete', old.id, old.content, old.key);
    INSERT INTO memories_fts(rowid, content, key)
    VALUES (new.id, new.content, new.key);
END;
"""


class KeyExistsError(Exception):
    """Raised by store() when a key already exists in memory."""


class Memory(NamedTuple):
    id:         int
    category:   str
    key:        str
    content:    str
    source:     str
    importance: int


class MemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    # ── Existence checks ──────────────────────────────────────────────────────

    def exists(self, key: str) -> bool:
        """Return True if a memory with this key exists."""
        row = self._conn.execute(
            "SELECT 1 FROM memories WHERE key = ?", (key,)
        ).fetchone()
        return row is not None

    def get(self, key: str) -> Memory | None:
        """Return the Memory for this key, or None if it does not exist."""
        row = self._conn.execute(
            "SELECT id, category, key, content, source, importance FROM memories WHERE key = ?",
            (key,),
        ).fetchone()
        return Memory(*row) if row else None

    # ── Write operations ──────────────────────────────────────────────────────

    def store(
        self,
        category:   str,
        key:        str,
        content:    str,
        source:     str = SOURCE_SESSION,
        importance: int = 3,
    ) -> None:
        """Insert a new memory. Raises KeyExistsError if the key already exists.

        Call exists() first if you need to check. To update an existing key
        use overwrite() or append().
        """
        self._validate(category, source, importance)
        try:
            self._conn.execute(
                "INSERT INTO memories (category, key, content, source, importance) VALUES (?, ?, ?, ?, ?)",
                (category, key, content, source, importance),
            )
            self._conn.commit()
        except sqlite3.IntegrityError:
            raise KeyExistsError(
                f"Key {key!r} already exists. Use overwrite() to replace or append() to add to it."
            )

    def overwrite(
        self,
        key:        str,
        content:    str,
        source:     str = SOURCE_SESSION,
        importance: int = None,
    ) -> None:
        """Replace the content of an existing memory.

        importance is unchanged if not provided.
        Raises KeyError if the key does not exist.
        """
        if not self.exists(key):
            raise KeyError(f"Key {key!r} not found. Use store() to create a new memory.")
        if source not in VALID_SOURCES:
            raise ValueError(f"source must be one of {sorted(VALID_SOURCES)}, got {source!r}")

        if importance is not None:
            if not 1 <= importance <= 5:
                raise ValueError(f"importance must be between 1 and 5, got {importance}")
            self._conn.execute(
                "UPDATE memories SET content = ?, source = ?, importance = ? WHERE key = ?",
                (content, source, importance, key),
            )
        else:
            self._conn.execute(
                "UPDATE memories SET content = ?, source = ? WHERE key = ?",
                (content, source, key),
            )
        self._conn.commit()

    def append(self, key: str, content: str, source: str = SOURCE_SESSION) -> None:
        """Append content to an existing memory, separated by a dated divider.

        Raises KeyError if the key does not exist.
        """
        if not self.exists(key):
            raise KeyError(f"Key {key!r} not found. Use store() to create a new memory.")
        if source not in VALID_SOURCES:
            raise ValueError(f"source must be one of {sorted(VALID_SOURCES)}, got {source!r}")

        date = datetime.utcnow().strftime("%Y-%m-%d")
        separator = f"{_APPEND_SEPARATOR}[appended {date}]\n"
        self._conn.execute(
            "UPDATE memories SET content = content || ?, source = ? WHERE key = ?",
            (separator + content, source, key),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        """Delete a memory by key. Silent if the key does not exist."""
        self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()

    # ── Read operations ───────────────────────────────────────────────────────

    def search(
        self,
        query:    str,
        top_k:   int = 5,
        category: str = None,
    ) -> list[Memory]:
        """Full-text search across memory content and keys.

        Tries the full query first (AND semantics). If nothing matches, falls
        back to searching each term individually, deduplicating by key and
        sorting by importance.
        """
        if category is not None and category not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got {category!r}"
            )
        results = self._search_fts(query, top_k, category)
        if results:
            return results
        seen = {}
        for term in query.split():
            if len(term) < 3:
                continue
            for m in self._search_fts(term, top_k, category):
                if m.key not in seen:
                    seen[m.key] = m
        return sorted(seen.values(), key=lambda m: m.importance, reverse=True)[:top_k]

    def _search_fts(self, query: str, top_k: int, category: str | None) -> list[Memory]:
        """Execute a single FTS5 MATCH query. Returns empty list on FTS syntax errors."""
        try:
            if category:
                rows = self._conn.execute(
                    """SELECT m.id, m.category, m.key, m.content, m.source, m.importance
                       FROM memories_fts f
                       JOIN memories m ON m.id = f.rowid
                       WHERE memories_fts MATCH ?
                         AND m.category = ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, category, top_k),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    """SELECT m.id, m.category, m.key, m.content, m.source, m.importance
                       FROM memories_fts f
                       JOIN memories m ON m.id = f.rowid
                       WHERE memories_fts MATCH ?
                       ORDER BY rank
                       LIMIT ?""",
                    (query, top_k),
                ).fetchall()
        except Exception:
            return []
        return [Memory(*r) for r in rows]

    def all(self, category: str = None) -> list[Memory]:
        """Return all memories, ordered by importance then recency."""
        if category:
            rows = self._conn.execute(
                """SELECT id, category, key, content, source, importance
                   FROM memories WHERE category = ?
                   ORDER BY importance DESC, created_at DESC""",
                (category,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                """SELECT id, category, key, content, source, importance
                   FROM memories
                   ORDER BY importance DESC, created_at DESC"""
            ).fetchall()
        return [Memory(*r) for r in rows]

    def close(self) -> None:
        self._conn.close()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _validate(self, category: str, source: str, importance: int) -> None:
        if category not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got {category!r}"
            )
        if source not in VALID_SOURCES:
            raise ValueError(
                f"source must be one of {sorted(VALID_SOURCES)}, got {source!r}"
            )
        if not 1 <= importance <= 5:
            raise ValueError(f"importance must be between 1 and 5, got {importance}")
