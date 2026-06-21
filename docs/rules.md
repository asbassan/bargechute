# bargechute — Agent Rules

This document is the human-readable reference for all procedural rules seeded
into the agent's memory. The agent loads these from SQLite (`procedural` category).
When rules change, update both this file and `scripts/seed_memory.py`.

---

## rule_coding_workflow

The agent must follow this order on every task — no exceptions:

1. **Search memory** for relevant knowledge before writing any code
2. **Read existing Barge source files** to understand the context
3. **Write or modify** Go files to implement the requirement
4. **Run `go build`** — fix all errors before proceeding
5. **Run `go test`** — fix all failures before proceeding
6. **Store what was learned** as an episodic memory

Do not skip steps. Do not consider a task done without passing build and tests.

---

## rule_memory_usage

When to search:
- Before every code change — always

When to store:
- After fixing a bug → `store_episodic`, key: `bug_NNN`
- After learning a new Barge pattern → `store_semantic`
- After a session ends → `store_episodic`, key: `session_NNN`

Importance guide:
- `5` — rules and critical facts (conventions, architectural decisions)
- `3` — supporting context (how a feature works)
- `1` — one-off observations

---

## rule_barge_go

Barge-specific rules the agent must always follow when writing Go:

- Never hardcode Windows paths — always use `toWindowsPath()`
- Never use `Type: "bind"` in OCI mounts — use empty string for VSMB
- Every new Runtime method needs: signature in `interface.go` + implementation on `*Client`
- New Bargefile instructions need changes in **both** `bargefile.go` AND `builder.go`
- Error messages must be user-friendly and include the exact fix command
- Always run `go vet ./...` before considering a change complete
