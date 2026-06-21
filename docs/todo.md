# bargechute TODO

Action items deferred for later. Complete items are moved to the bottom.

## Pending

### PR Review Loop (next GitHub milestone)

- **Agent reads PR review comments and iterates** — After the agent creates a PR, the user or reviewer leaves comments on the diff. Add a `get_pr_comments(pr_number)` tool (`gh pr view N --json reviews,comments --repo asbassan/barge`) so the agent can read review feedback, make the requested changes on the same branch, commit, push (PR auto-updates), and reply that the changes are addressed. Closes the human-in-the-loop cycle: issue → PR → review → fix → re-review → merge.

### Sessions (UX — not blocking first bug fix)

- **sessions.py** — Session registry module. `sessions` table in `bargechute.db` with `name TEXT PRIMARY KEY, created_at INTEGER`. Methods: `create(name)`, `list()`, `exists(name)`. Session name is used directly as LangGraph `thread_id`.

- **repl.py updates** — On startup: show recent sessions, offer `resume <name>` or `new`. On `new`: prompt "Session name? (Enter to auto-generate as YYYYMMDD_HHMMSS)". Call `sessions.create(name)` when a new session begins.

- **commands.py updates** — Add `!sessions` (list all sessions with name + date) and `!resume <name>` (switch active session mid-REPL, loading its full message history via LangGraph checkpoint).

### Logging

- **Agent action logging** — Currently there is no file-based log of what the agent does. Tool calls, arguments, and results are invisible after the session ends. Add a session log file (`data/logs/YYYYMMDD_HHMMSS.log`) that records every tool call name, input, and output as it happens. Implement as a LangGraph callback or a wrapper around `ToolNode`. Critical for debugging when the agent goes wrong — without it you are flying blind.

### Documentation

- **docs/api.md — Agent tool API reference** — Deep reference doc for each tool: parameters, return format, error cases, and when to use it vs alternatives. Complements `tools_list.md` (catalogue) with implementation-level detail. Useful for tuning the system prompt and debugging agent behaviour.

### Packaging

- **`bargechute` CLI entry point** — Add `[project.scripts] bargechute = "repl:run"` to `pyproject.toml`. After `pip install -e .` the agent starts with `bargechute` from any directory. Also fix `requires-python = ">=3.11"` → `">=3.10"` to match the running environment (Python 3.10.11).

### Architecture (deferred refactors)

- **Split SQL schema out of memory.py** — `_SCHEMA` string in `memory.py` hides the DB structure inside Python. Create a `sqlscripts/` folder with one `.sql` file per table (e.g. `memories.sql`, `sessions.sql`). `memory.py` and `sessions.py` load and execute them rather than embedding DDL. Natural trigger: when `sessions.py` is introduced (two schema owners = the mess starts).

- **Extract DB connection into db.py** — `memory.py` currently owns the SQLite connection and commit lifecycle. When a third module needs the DB this becomes a problem. A thin `db.py` that opens the connection and runs schema files, then passes the connection to `memory.py` / `sessions.py`, keeps each module focused on its own table.

- **Working memory trimming** — `MessagesState` grows unboundedly within a session. Long sessions will eventually exceed the LLM context window. Add message trimming (keep last N turns, or summarise older turns into a single system message) when this becomes a practical problem.

- **Vector/embedding search (phase 2)** — Current `search()` uses SQLite FTS5 (keyword match). Phase 2: add embedding-based semantic search alongside FTS. Candidate: `sqlite-vec` extension or a separate ChromaDB store. No embeddings until text-only retrieval proves insufficient.

## Completed

<!-- Move items here with a completion date when done -->
