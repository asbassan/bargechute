"""Handles ! commands typed directly by the user in the REPL.

These bypass the LLM and write directly to memory — no classification guesswork.

Commands:
  !remember <semantic|episodic|procedural> <key> <content>
  !list [semantic|episodic|procedural]
  !delete <key>
  !search <query>
  !help
"""
from memory import MemoryStore, VALID_CATEGORIES, SOURCE_SESSION


_COMMAND_NAMES = {"remember", "list", "search", "delete", "help"}


def handle(line: str, store: MemoryStore) -> str | None:
    """Return a response string if line is a ! command, None otherwise."""
    if not line.startswith("!"):
        first = line.strip().split()[0].lower() if line.strip() else ""
        if first in _COMMAND_NAMES:
            return f"Did you mean '!{line.strip()}'? Commands require the ! prefix."
        return None

    parts = line[1:].strip().split(None, 3)
    if not parts:
        return "Type !help for available commands."

    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "remember":
        return _remember(args, store)
    if cmd == "list":
        return _list(args, store)
    if cmd == "delete":
        return _delete(args, store)
    if cmd == "search":
        return _search(args, store)
    if cmd == "help":
        return _help()

    return f"Unknown command: !{cmd}\nType !help for available commands."


def _remember(args: list[str], store: MemoryStore) -> str:
    if len(args) < 3:
        return "Usage: !remember <semantic|episodic|procedural> <key> <content>"
    category, key, content = args[0].lower(), args[1], args[2]
    if category not in VALID_CATEGORIES:
        return f"Invalid category '{category}'. Must be one of: {sorted(VALID_CATEGORIES)}"
    store.store(category, key, content, source=SOURCE_SESSION)
    return f"Stored: {category}/{key}"


def _list(args: list[str], store: MemoryStore) -> str:
    category = args[0].lower() if args else None
    if category and category not in VALID_CATEGORIES:
        return f"Invalid category '{category}'. Must be one of: {sorted(VALID_CATEGORIES)}"
    memories = store.all(category=category)
    if not memories:
        label = f"'{category}'" if category else "any"
        return f"No memories found for category: {label}"
    lines = []
    for m in memories:
        lines.append(f"[{m.category}] {m.key}  importance={m.importance}  source={m.source}")
        preview = m.content[:120].replace("\n", " ")
        lines.append(f"  {preview}{'...' if len(m.content) > 120 else ''}")
    return "\n".join(lines)


def _delete(args: list[str], store: MemoryStore) -> str:
    if not args:
        return "Usage: !delete <key>"
    store.delete(args[0])
    return f"Deleted: {args[0]}"


def _search(args: list[str], store: MemoryStore) -> str:
    if not args:
        return "Usage: !search <query>"
    query = " ".join(args)
    results = store.search(query, top_k=5)
    if not results:
        return f"No memories found for: {query!r}"
    lines = []
    for m in results:
        lines.append(f"[{m.category}/{m.key}] importance={m.importance}")
        lines.append(f"  {m.content[:200].replace(chr(10), ' ')}")
    return "\n".join(lines)


def _help() -> str:
    return """Available commands:
  !remember <semantic|episodic|procedural> <key> <content>
      Write directly to memory — bypasses the LLM
  !list [semantic|episodic|procedural]
      Show all stored memories, optionally filtered by category
  !search <query>
      Search memory with a keyword query
  !delete <key>
      Remove a memory by key
  !help
      Show this message"""
