import subprocess
from langchain_core.tools import tool
from config import BARGE_PATH
from memory import MemoryStore, SEMANTIC, EPISODIC, PROCEDURAL, SOURCE_SESSION

_store = MemoryStore()


# ── Memory tools ──────────────────────────────────────────────────────────────

@tool
def search_memory(query: str) -> str:
    """Search long-term memory for relevant Barge knowledge."""
    results = _store.search(query, top_k=5)
    if not results:
        return "No relevant memories found."
    return "\n\n".join(
        f"[{m.category}/{m.key}] (importance={m.importance})\n{m.content}"
        for m in results
    )


@tool
def store_semantic(key: str, content: str, importance: int = 3) -> str:
    """Store a Barge fact, convention, or architectural knowledge.

    Use for: code conventions, how a feature works, architectural decisions.
    key: unique slug, e.g. 'barge_copy_requires_powershell'
    importance: 1 (low) to 5 (critical), default 3
    """
    _store.store(SEMANTIC, key, content, source=SOURCE_SESSION, importance=importance)
    return f"Stored semantic memory: {key}"


@tool
def store_episodic(key: str, content: str, importance: int = 3) -> str:
    """Store a past experience: a bug fix, session outcome, or what was tried.

    Use for: bug fixes, build errors and their solutions, failed approaches.
    key: unique slug, e.g. 'bug_001' or 'session_3'
    importance: 1 (low) to 5 (critical), default 3
    """
    _store.store(EPISODIC, key, content, source=SOURCE_SESSION, importance=importance)
    return f"Stored episodic memory: {key}"


@tool
def store_procedural(key: str, content: str, importance: int = 5) -> str:
    """Store a rule the agent must always follow when coding Barge.

    Use for: workflow rules, coding constraints, things that must never be done.
    key: unique slug, e.g. 'rule_always_test'
    importance: defaults to 5 — procedural rules are highest priority
    """
    _store.store(PROCEDURAL, key, content, source=SOURCE_SESSION, importance=importance)
    return f"Stored procedural memory: {key}"


# ── Barge repository tools ────────────────────────────────────────────────────

@tool
def go_build(target: str = "./cmd/barge") -> str:
    """Run go build on the Barge repository."""
    result = subprocess.run(
        ["go", "build", target],
        cwd=str(BARGE_PATH),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        return f"Build succeeded: {target}"
    return f"Build failed:\n{result.stderr}"


@tool
def go_test(pkg: str = "./...") -> str:
    """Run go test on the Barge repository."""
    result = subprocess.run(
        ["go", "test", pkg],
        cwd=str(BARGE_PATH),
        capture_output=True,
        text=True,
        timeout=120,
    )
    output = result.stdout + result.stderr
    return output if output else "Tests passed with no output."


@tool
def read_file(relative_path: str) -> str:
    """Read a file from the Barge repository. Path is relative to the Barge root."""
    path = BARGE_PATH / relative_path
    if not path.exists():
        return f"File not found: {relative_path}"
    return path.read_text(encoding="utf-8")


@tool
def write_file(relative_path: str, content: str) -> str:
    """Write content to a file in the Barge repository. Creates parent directories if needed."""
    path = (BARGE_PATH / relative_path).resolve()
    if not str(path).startswith(str(BARGE_PATH.resolve())):
        return f"Error: path {relative_path!r} is outside the Barge repository"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Written: {relative_path} ({len(content)} bytes)"


@tool
def list_files(subdir: str = "") -> str:
    """List files in the Barge repository. subdir is relative to the Barge root."""
    path = BARGE_PATH / subdir if subdir else BARGE_PATH
    if not path.exists():
        return f"Directory not found: {subdir}"
    entries = sorted(path.rglob("*.go")) if not subdir else sorted(path.iterdir())
    if not entries:
        return "No files found."
    return "\n".join(str(e.relative_to(BARGE_PATH)) for e in entries)


TOOLS = [
    search_memory,
    store_semantic,
    store_episodic,
    store_procedural,
    go_build,
    go_test,
    read_file,
    write_file,
    list_files,
]
