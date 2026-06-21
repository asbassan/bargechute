"""Seed bargechute with foundational Barge knowledge."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryStore, SEMANTIC, PROCEDURAL, SOURCE_SEED

# (category, key, content, importance)
MEMORIES = [

    # ── Semantic: core facts ──────────────────────────────────────────────────

    (SEMANTIC, "barge_overview",
     """Barge is a Windows container runtime written in Go.
Module: github.com/asbassan/barge
Entry point: cmd/barge/main.go
Runtime backend: containerd + runhcs (Hyper-V isolation)
Containerd namespace: 'barge'
Snapshotter: 'windows'
HV runtime: 'io.containerd.runhcs.v1'""", 5),

    (SEMANTIC, "barge_packages",
     """Internal packages:
- internal/client    — containerd wrapper (run, pull, exec, commit, push, login, logs)
- internal/build     — Bargefile parser + builder
- internal/network   — HCN NAT network (barge-nat)
- internal/output    — coloured CLI output helpers
- internal/preflight — startup checks (containerd running, barge-nat exists)""", 5),

    (SEMANTIC, "barge_file_structure",
     """Key files in each package:
internal/client/
  interface.go   — Runtime interface (all operations defined here)
  client.go      — New() constructor, ctx() helper, Version()
  run.go         — Run(), parseMappedDirectories(), parsePortMappings()
  container.go   — ListContainers(), StopContainer(), RemoveContainer(), Logs(), Exec()
  images.go      — Pull(), ListImages(), RemoveImage(), TagImage(), PushImage()
  commit.go      — CommitContainer(), CommitOptions struct
  auth.go        — Login(), Logout(), credentialsForHost()
  stats.go       — Stats()
internal/build/
  bargefile.go   — Parse(), Instruction, InstructionType constants
  builder.go     — Builder.Build(), execCopy(), execRun(), substituteArgs()
  fileserver.go  — newFileServer(), zipDir()
internal/network/
  hcn.go         — EnsureNATNetwork(), CreateEndpoint(), DeleteEndpoint(), GatewayIP()
internal/output/
  output.go      — Infof(), Successf(), Errorf(), Warnf(), PrintTable()
internal/preflight/
  check.go       — Check(), ContainerdAddress()
cmd/barge/
  main.go        — buildRoot(), all newXxxCmd() functions, readEnvFile()""", 5),

    (SEMANTIC, "bargefile_instructions",
     """Supported Bargefile instructions:
FROM <image>         — base image, must be first
ARG NAME=default     — build-time variable with optional default
WORKDIR /path        — working directory for RUN
COPY src dst         — copies host dir via HTTP zip (requires PowerShell in image)
RUN <cmd>            — runs via cmd.exe, respects WORKDIR
ENV KEY=VALUE        — environment variable baked into image
EXPOSE 80 443        — documents ports (multiple allowed)
CMD ["exe", "args"]  — default command, JSON array or plain text
Not supported: ENTRYPOINT, LABEL, VOLUME, USER, HEALTHCHECK, SHELL""", 4),

    (SEMANTIC, "barge_add_bargefile_instruction",
     """How to add a new Bargefile instruction (e.g. LABEL):
Step 1 — internal/build/bargefile.go
  Add constant:   InstrLABEL InstructionType = "LABEL"
  Add case in Parse() switch:
    case InstrLABEL:
        args = []string{rest}   (or strings.Fields(rest) for multiple args)

Step 2 — internal/build/builder.go
  Add case in Build() loop:
    case InstrLABEL:
        value := substituteArgs(instr.Args[0], state.args)
        output.Infof("Step %d/N: LABEL %s", step, value)
        step++
  If it affects the committed image, pass it through CommitOptions.

Step 3 — internal/build/bargefile_test.go
  Add a test case in TestParse() for the new instruction.""", 5),

    (SEMANTIC, "barge_add_cli_command",
     """How to add a new CLI command (e.g. barge inspect):
Step 1 — cmd/barge/main.go
  Write a constructor function following the existing pattern:
    func newInspectCmd() *cobra.Command {
        cmd := &cobra.Command{
            Use:   "inspect <id>",
            Short: "Show details of a container",
            Args:  cobra.ExactArgs(1),
            RunE: func(cmd *cobra.Command, args []string) error {
                cl, err := client.New()
                if err != nil { return err }
                defer cl.Close()
                // call cl.SomeMethod(ctx, args[0])
            },
        }
        return cmd
    }

Step 2 — register in buildRoot():
  root.AddCommand(newInspectCmd())

Step 3 — internal/client/interface.go
  Add the method signature to the Runtime interface.

Step 4 — implement the method in the appropriate internal/client/*.go file.""", 5),

    (SEMANTIC, "barge_runtime_interface",
     """The Runtime interface lives in internal/client/interface.go.
Every external operation in Barge is defined here.
The concrete type is *Client (internal/client/client.go).
Compile-time check ensures Client always satisfies the interface:
  var _ Runtime = (*Client)(nil)

Adding a new operation requires:
1. Add method signature to Runtime interface
2. Implement the method on *Client in the appropriate file
3. The compile-time check will catch any drift at build time""", 5),

    (SEMANTIC, "barge_test_structure",
     """Barge test conventions:
- Test files live next to the code: internal/build/bargefile_test.go
- Same package as the code being tested (package build, not package build_test)
- Table-driven tests using []struct{ name, input, want } pattern
- No mocks — tests call real functions directly
- Test helpers use t.Helper() so failures point to the call site
- Run all tests: go test ./...
- Run one package: go test ./internal/build/...
- Test file naming: <filename>_test.go""", 4),

    (SEMANTIC, "barge_error_pattern",
     """Barge error formatting conventions:
Two-layer pattern in CLI (main.go):
  Layer 1: output.Errorf() — coloured message to stderr with ✗ prefix
  Layer 2: return fmt.Errorf("") — empty error suppresses Cobra's duplicate print

User-facing errors must include a fix command:
  return fmt.Errorf(
      "container %q not running\\n\\n"+
      "  Start it with: barge run %s",
      id, id,
  )

Internal errors wrap with context:
  return fmt.Errorf("FROM: %w", err)
  return fmt.Errorf("cannot stop build container: %w", err)

containerNotFound() helper in container.go returns a standard not-found message.""", 4),

    (SEMANTIC, "barge_conventions",
     """Barge Go code conventions:
- No comments unless the WHY is non-obvious
- No over-engineering — three similar lines beats a premature abstraction
- Error messages are user-friendly with exact fix commands
- All external operations go through the Runtime interface (internal/client/interface.go)
- Tests live next to the code they test (_test.go, same package)
- Windows paths use toWindowsPath() — never hardcode backslashes
- Container labels: barge.logfile (log path), barge.endpoint (HCN endpoint ID)
- New instructions must be added to: bargefile.go (parser) + builder.go (executor)""", 5),

    (SEMANTIC, "barge_networking",
     """Barge networking uses HCN (Host Compute Network) — Windows-native.
Network name: barge-nat (NAT type)
All containers share this network and can reach each other by IP.
OCI Mount.Type must be empty string — NOT 'bind' — for VSMB mounts to work.
runhcs (containerd shim) converts empty Type to VSMB for Hyper-V isolation.
Port publishing: HCN port-mapping policies on the endpoint.
GatewayIP() returns host NAT IP — used by build COPY to serve files.""", 4),

    (SEMANTIC, "barge_images",
     """Barge only runs Windows container images (windows/amd64).
Linux images are rejected at runtime.
For COPY in Bargefile: base image must have PowerShell (ServerCore-based).
NanoServer has no PowerShell — cannot use COPY with NanoServer base.
Registries: MCR (mcr.microsoft.com), Docker Hub, private (barge login first).
Common base: mcr.microsoft.com/windows/servercore:ltsc2022""", 4),

    # ── Procedural: rules the agent must always follow ────────────────────────

    (PROCEDURAL, "rule_coding_workflow",
     """Agent coding workflow — follow this order on every task:
1. Search memory for relevant knowledge before writing any code
2. Read existing Barge source files to understand context
3. Write or modify Go files to implement the requirement
4. Run go build — fix all errors before proceeding
5. Run go test — fix all failures before proceeding
6. Store what was learned as an episodic memory
Do not skip steps. Do not commit without passing build and tests.""", 5),

    (PROCEDURAL, "rule_memory_usage",
     """Memory rules:
- Always call search_memory before writing any code
- After fixing a bug: store it as episodic memory with key bug_NNN
- After learning a new Barge pattern: store it as semantic memory
- After a session: store a summary as episodic memory with key session_NNN
- Use importance=5 for rules and critical facts
- Use importance=3 for supporting context
- Use importance=1 for one-off observations""", 5),

    (PROCEDURAL, "rule_barge_go",
     """Barge-specific Go rules the agent must follow:
- Never hardcode Windows paths — always use toWindowsPath()
- Never use Type: 'bind' in OCI mounts — use empty string for VSMB
- Every new Runtime method needs: interface.go signature + *Client implementation
- New Bargefile instructions need changes in BOTH bargefile.go AND builder.go
- Error messages must be user-friendly and include the fix command
- Always run go vet ./... before considering a change complete""", 5),
]


def main():
    store = MemoryStore()
    created = updated = 0
    for category, key, content, importance in MEMORIES:
        if store.exists(key):
            store.overwrite(key, content, source=SOURCE_SEED, importance=importance)
            print(f"  updated: {category}/{key} (importance={importance})")
            updated += 1
        else:
            store.store(category, key, content, source=SOURCE_SEED, importance=importance)
            print(f"  stored:  {category}/{key} (importance={importance})")
            created += 1
    print(f"\nDone — {created} created, {updated} updated.")


if __name__ == "__main__":
    main()
