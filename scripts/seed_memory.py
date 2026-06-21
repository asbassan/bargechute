"""Seed bargechute with foundational Barge knowledge."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from memory import MemoryStore

MEMORIES = [
    ("semantic", "barge_overview",
     """Barge is a Windows container runtime written in Go.
Module: github.com/asbassan/barge
Entry point: cmd/barge/main.go
Runtime backend: containerd + runhcs (Hyper-V isolation)
Containerd namespace: 'barge'
Snapshotter: 'windows'
HV runtime: 'io.containerd.runhcs.v1'"""),

    ("semantic", "barge_packages",
     """Internal packages:
- internal/client    — containerd wrapper (run, pull, exec, commit, push, login, logs)
- internal/build     — Bargefile parser + builder
- internal/network   — HCN NAT network (barge-nat)
- internal/output    — coloured CLI output helpers
- internal/preflight — startup checks (containerd running, barge-nat exists)"""),

    ("semantic", "bargefile_instructions",
     """Supported Bargefile instructions:
FROM <image>         — base image, must be first
ARG NAME=default     — build-time variable with optional default
WORKDIR /path        — working directory for RUN
COPY src dst         — copies host dir via HTTP zip (requires PowerShell in image)
RUN <cmd>            — runs via cmd.exe, respects WORKDIR
ENV KEY=VALUE        — environment variable baked into image
EXPOSE 80 443        — documents ports (multiple allowed)
CMD ["exe", "args"]  — default command, JSON array or plain text
Not supported: ENTRYPOINT, LABEL, VOLUME, USER, HEALTHCHECK, SHELL"""),

    ("semantic", "barge_conventions",
     """Barge Go code conventions:
- No comments unless the WHY is non-obvious
- No over-engineering — three similar lines beats a premature abstraction
- Error messages are user-friendly with exact fix commands
- All external operations go through the Runtime interface (internal/client/interface.go)
- Tests live next to the code they test (_test.go, same package)
- Windows paths use toWindowsPath() — never hardcode backslashes
- Container labels: barge.logfile (log path), barge.endpoint (HCN endpoint ID)
- New instructions must be added to: bargefile.go (parser) + builder.go (executor)"""),

    ("semantic", "barge_networking",
     """Barge networking uses HCN (Host Compute Network) — Windows-native.
Network name: barge-nat (NAT type)
All containers share this network and can reach each other by IP.
OCI Mount.Type must be empty string — NOT 'bind' — for VSMB mounts to work.
runhcs (containerd shim) converts empty Type to VSMB for Hyper-V isolation.
Port publishing: HCN port-mapping policies on the endpoint.
GatewayIP() returns host NAT IP — used by build COPY to serve files."""),

    ("semantic", "barge_images",
     """Barge only runs Windows container images (windows/amd64).
Linux images are rejected at runtime.
For COPY in Bargefile: base image must have PowerShell (ServerCore-based).
NanoServer has no PowerShell — cannot use COPY with NanoServer base.
Registries: MCR (mcr.microsoft.com), Docker Hub, private (barge login first).
Common base: mcr.microsoft.com/windows/servercore:ltsc2022"""),
]


def main():
    store = MemoryStore()
    for category, key, content in MEMORIES:
        store.store(category, key, content)
        print(f"  stored: {category}/{key}")
    print(f"\nSeeded {len(MEMORIES)} memories.")


if __name__ == "__main__":
    main()
