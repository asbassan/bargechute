# bargechute TODO

Action items deferred for later. Complete items are moved to the bottom.

## Pending

- **Split SQL schema out of memory.py** — `_SCHEMA` string in `memory.py` hides the DB structure inside Python. Create a `sqlscripts/` folder with one `.sql` file per table (e.g. `memories.sql`, `sessions.sql`). `memory.py` and `sessions.py` load and execute them rather than embedding DDL. Natural trigger: when `sessions.py` is introduced (two schema owners = the mess starts).

- **Extract DB connection into db.py** — `memory.py` currently owns the SQLite connection and commit lifecycle. When a third module needs the DB this becomes a problem. A thin `db.py` that opens the connection and runs schema files, then passes the connection to `memory.py` / `sessions.py`, keeps each module focused on its own table.

- **Working memory trimming** — `MessagesState` grows unboundedly within a session. Long sessions will eventually exceed the LLM context window. Add message trimming (keep last N turns, or summarise older turns into a single system message) when this becomes a practical problem.

- **Vector/embedding search (phase 2)** — Current `search()` uses SQLite FTS5 (keyword match). Phase 2: add embedding-based semantic search alongside FTS. Candidate: `sqlite-vec` extension or a separate ChromaDB store. No embeddings until text-only retrieval proves insufficient.

## Completed

<!-- Move items here with a completion date when done -->
