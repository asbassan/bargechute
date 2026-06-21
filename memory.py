import sqlite3
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

    def store(
        self,
        category:   str,
        key:        str,
        content:    str,
        source:     str = SOURCE_SEED,
        importance: int = 3,
    ) -> None:
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

        self._conn.execute(
            """INSERT INTO memories (category, key, content, source, importance)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
                   category   = excluded.category,
                   content    = excluded.content,
                   source     = excluded.source,
                   importance = excluded.importance""",
            (category, key, content, source, importance),
        )
        self._conn.commit()

    def search(
        self,
        query:    str,
        top_k:   int = 5,
        category: str = None,
    ) -> list[Memory]:
        if category is not None and category not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got {category!r}"
            )

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

        return [Memory(*r) for r in rows]

    def all(self, category: str = None) -> list[Memory]:
        if category:
            rows = self._conn.execute(
                """SELECT id, category, key, content, source, importance
                   FROM memories
                   WHERE category = ?
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

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
