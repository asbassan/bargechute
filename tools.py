import subprocess
from langchain_core.tools import tool
from config import BARGE_PATH
from memory import MemoryStore

_store = MemoryStore()


@tool
def search_memory(query: str) -> str:
    """Search long-term memory for relevant Barge knowledge."""
    results = _store.search(query, top_k=5)
    if not results:
        return "No relevant memories found."
    return "\n\n".join(f"[{m.category}/{m.key}]\n{m.content}" for m in results)


@tool
def store_memory(category: str, key: str, content: str) -> str:
    """Store knowledge about Barge into long-term memory.

    category: 'semantic' (facts/conventions), 'episodic' (past fixes), 'procedural' (rules)
    key: unique slug, e.g. 'bargefile_copy_instruction'
    content: the knowledge to store
    """
    _store.store(category, key, content)
    return f"Stored: {category}/{key}"


@tool
def go_build(target: str = "./cmd/barge") -> str:
    """Run go build on the Barge repository."""
    result = subprocess.run(
        ["go", "build", target],
        cwd=str(BARGE_PATH),
        capture_output=True,
        text=True,
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
    path = BARGE_PATH / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return f"Written: {relative_path} ({len(content)} bytes)"


TOOLS = [search_memory, store_memory, go_build, go_test, read_file, write_file]
