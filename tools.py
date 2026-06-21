import json
import subprocess
from langchain_core.tools import tool
from config import BARGE_PATH, GITHUB_REPO
from memory import MemoryStore, SEMANTIC, EPISODIC, PROCEDURAL, SOURCE_SESSION, KeyExistsError

_store = MemoryStore()


def _conflict_message(key: str, existing, proposed: str) -> str:
    preview = existing.content if len(existing.content) <= 300 else existing.content[:300] + "..."
    return (
        f"KEY EXISTS: key={key!r} ({existing.category}, importance={existing.importance})\n"
        f"Current content:\n{preview}\n\n"
        f"Proposed content:\n{proposed}\n\n"
        f"Ask the user: overwrite / append / cancel"
    )


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
    try:
        _store.store(SEMANTIC, key, content, source=SOURCE_SESSION, importance=importance)
        return f"Stored semantic memory: {key}"
    except KeyExistsError:
        return _conflict_message(key, _store.get(key), content)


@tool
def store_episodic(key: str, content: str, importance: int = 3) -> str:
    """Store a past experience: a bug fix, session outcome, or what was tried.

    Use for: bug fixes, build errors and their solutions, failed approaches.
    key: unique slug, e.g. 'bug_001' or 'session_3'
    importance: 1 (low) to 5 (critical), default 3
    """
    try:
        _store.store(EPISODIC, key, content, source=SOURCE_SESSION, importance=importance)
        return f"Stored episodic memory: {key}"
    except KeyExistsError:
        return _conflict_message(key, _store.get(key), content)


@tool
def store_procedural(key: str, content: str, importance: int = 5) -> str:
    """Store a rule the agent must always follow when coding Barge.

    Use for: workflow rules, coding constraints, things that must never be done.
    key: unique slug, e.g. 'rule_always_test'
    importance: defaults to 5 — procedural rules are highest priority
    """
    try:
        _store.store(PROCEDURAL, key, content, source=SOURCE_SESSION, importance=importance)
        return f"Stored procedural memory: {key}"
    except KeyExistsError:
        return _conflict_message(key, _store.get(key), content)


@tool
def overwrite_memory(key: str, content: str) -> str:
    """Replace an existing memory. Only call after the user has confirmed overwrite."""
    try:
        _store.overwrite(key, content, source=SOURCE_SESSION)
        return f"Overwritten: {key}"
    except KeyError:
        return f"Key {key!r} not found."


@tool
def append_memory(key: str, content: str) -> str:
    """Append to an existing memory. Only call after the user has confirmed append."""
    try:
        _store.append(key, content, source=SOURCE_SESSION)
        return f"Appended to: {key}"
    except KeyError:
        return f"Key {key!r} not found."


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


# ── GitHub / Git tools ───────────────────────────────────────────────────────

@tool
def get_issue(issue_number: int) -> str:
    """Read a GitHub issue from the Barge repository."""
    result = subprocess.run(
        ["gh", "issue", "view", str(issue_number),
         "--json", "title,body", "--repo", GITHUB_REPO],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return f"Failed to fetch issue {issue_number}:\n{result.stderr}"
    data = json.loads(result.stdout)
    return f"Issue #{issue_number}: {data['title']}\n\n{data['body']}"


@tool
def create_branch(branch_name: str) -> str:
    """Create and switch to a new git branch in the Barge repository.

    Use naming convention: fix/issue-N-short-description
    Always call this before making any file changes.
    """
    checkout = subprocess.run(
        ["git", "checkout", "master"],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=15,
    )
    if checkout.returncode != 0:
        return f"Failed to checkout master:\n{checkout.stderr}"
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        return f"Failed to create branch {branch_name!r}:\n{result.stderr}"
    return f"Created and switched to branch: {branch_name}"


@tool
def git_commit(message: str) -> str:
    """Stage all changes and commit in the Barge repository."""
    add = subprocess.run(
        ["git", "add", "-A"],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=15,
    )
    if add.returncode != 0:
        return f"git add failed:\n{add.stderr}"
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        return f"git commit failed:\n{result.stderr}"
    return f"Committed: {message}"


@tool
def create_pr(title: str, body: str) -> str:
    """Push the current branch and open a pull request against master.

    Always call git_commit before this tool.
    """
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=10,
    ).stdout.strip()
    if not branch or branch == "master":
        return "Error: cannot create PR from master — call create_branch first."
    push = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=30,
    )
    if push.returncode != 0:
        return f"git push failed:\n{push.stderr}"
    result = subprocess.run(
        ["gh", "pr", "create", "--title", title, "--body", body,
         "--repo", GITHUB_REPO],
        cwd=str(BARGE_PATH), capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return f"PR creation failed:\n{result.stderr}"
    return f"PR created: {result.stdout.strip()}"


TOOLS = [
    search_memory,
    store_semantic,
    store_episodic,
    store_procedural,
    overwrite_memory,
    append_memory,
    get_issue,
    create_branch,
    git_commit,
    create_pr,
    go_build,
    go_test,
    read_file,
    write_file,
    list_files,
]
