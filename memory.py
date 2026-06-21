import sqlite3
from pathlib import Path
from typing import NamedTuple

from config import DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    id         INTEGER PRIMARY KEY,
    category   TEXT    NOT NULL,
    key        TEXT    NOT NULL UNIQUE,
    content    TEXT    NOT NULL,
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
    id: int
    category: str
    key: str
    content: str


class MemoryStore:
    def __init__(self, db_path: Path = DB_PATH):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def store(self, category: str, key: str, content: str) -> None:
        self._conn.execute(
            """INSERT INTO memories (category, key, content) VALUES (?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
                   content = excluded.content,
                   category = excluded.category""",
            (category, key, content),
        )
        self._conn.commit()

    def search(self, query: str, top_k: int = 5) -> list[Memory]:
        rows = self._conn.execute(
            """SELECT m.id, m.category, m.key, m.content
               FROM memories_fts f
               JOIN memories m ON m.id = f.rowid
               WHERE memories_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, top_k),
        ).fetchall()
        return [Memory(*r) for r in rows]

    def all(self) -> list[Memory]:
        rows = self._conn.execute(
            "SELECT id, category, key, content FROM memories ORDER BY created_at DESC"
        ).fetchall()
        return [Memory(*r) for r in rows]

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
