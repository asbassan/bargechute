# bargechute Memory Keys

All memory keys in bargechute. Keys are unique across all categories. Seeded keys (source=seed) are stable reference facts; session keys accumulate over time.

## Semantic Keys (facts, architecture, conventions)

| Key | Description | Source |
|-----|-------------|--------|
| `barge_overview` | Module path, entry point, runtime backend, containerd namespace | seed |
| `barge_packages` | Internal packages: client, build, network, output, preflight | seed |
| `barge_file_structure` | Key files in each package with their responsibilities | seed |
| `bargefile_instructions` | Supported Bargefile instructions and their syntax | seed |
| `barge_add_bargefile_instruction` | Step-by-step guide for adding a new Bargefile instruction | seed |
| `barge_add_cli_command` | Step-by-step guide for adding a new CLI command | seed |
| `barge_runtime_interface` | Runtime interface in interface.go, compile-time check pattern | seed |
| `barge_test_structure` | Test conventions: location, package, table-driven, no mocks | seed |
| `barge_error_pattern` | Two-layer error pattern: output.Errorf + empty fmt.Errorf | seed |
| `barge_conventions` | General Go conventions: no comments, no over-engineering, paths | seed |
| `barge_networking` | HCN networking, barge-nat, VSMB mounts, OCI Mount.Type empty | seed |
| `barge_images` | Windows-only images, PowerShell requirement for COPY, registries | seed |

## Procedural Keys (rules the agent must always follow)

| Key | Description | Source |
|-----|-------------|--------|
| `rule_coding_workflow` | Order of operations: search → read → write → build → test → store | seed |
| `rule_memory_usage` | When to write memory: bugs as episodic, patterns as semantic | seed |
| `rule_barge_go` | Barge-specific Go rules: paths, mounts, interface, instructions | seed |

## Episodic Keys (past sessions, bug fixes — accumulate over time)

No episodic memories are seeded. They are written by the agent during sessions.

Convention:
- `session_NNN` — end-of-session summaries written by the end-of-session hook
- `bug_NNN` — bug fixes with root cause and resolution
