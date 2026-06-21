# bargechute Tool List

Tools available to the bargechute agent. Each tool maps to a specific operation in the memory layer or the Barge codebase.

## Memory Tools

| Tool | Purpose | When to use |
|------|---------|-------------|
| `search_memory` | Full-text search across all memory content and keys | Always call first before writing any code or storing new memory |
| `store_semantic` | Store a new semantic memory (facts, architecture, conventions) | New key only — returns conflict info if key already exists |
| `store_episodic` | Store a new episodic memory (past sessions, bug fixes, what was tried) | New key only — returns conflict info if key already exists |
| `store_procedural` | Store a new procedural memory (rules the agent must always follow) | New key only — returns conflict info if key already exists |
| `overwrite_memory` | Replace the content of an existing memory | Only after user confirms overwrite on a conflict |
| `append_memory` | Append content to an existing memory with a dated separator | Only after user confirms append on a conflict |

## Codebase Tools

| Tool | Purpose |
|------|---------|
| `read_file` | Read a Go source file from the Barge repo |
| `write_file` | Write or update a Go source file (path must be inside BARGE_PATH) |
| `list_files` | List .go files or directory contents in the Barge repo |
| `go_build` | Run `go build ./...` in the Barge repo |
| `go_test` | Run `go test ./...` in the Barge repo |

## Conflict Handling Flow

When a `store_*` tool encounters an existing key it returns:

```
KEY EXISTS: key='<key>' (<category>, importance=<N>)
Current content: "<existing content>"
Proposed content: "<new content>"
Reply with: overwrite / append / cancel
```

The agent surfaces this to the user. On the next turn the agent calls `overwrite_memory` or `append_memory` based on the user's reply. The agent never overwrites memory automatically.
