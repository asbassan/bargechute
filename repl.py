"""REPL loop for bargechute.

Routes user input to:
  ! commands  → commands.handle()   (direct memory writes, no LLM)
  new / exit  → session lifecycle   (end-of-session hook, fresh thread)
  everything else → agent.chat()    (LangGraph + Ollama)
"""
import re
from agent import chat
from commands import handle
from hooks import end_of_session
from memory import MemoryStore

_BANNER = """bargechute — Barge coding agent
Type !help for commands | 'new' for a fresh session | 'exit' to quit
"""


def run() -> None:
    print(_BANNER)

    store = MemoryStore()
    session_count = 1
    session_id = f"session_{session_count}"
    session_messages: list[tuple[str, str]] = []

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            _close_session(session_id, session_messages, store)
            print("\nBye.")
            break

        if not user_input:
            continue

        if user_input.lower() == "exit":
            _close_session(session_id, session_messages, store)
            print("Bye.")
            break

        if user_input.lower() == "new":
            _close_session(session_id, session_messages, store)
            session_count += 1
            session_id = f"session_{session_count}"
            session_messages = []
            print(f"\nStarted: {session_id}\n")
            continue

        # ! commands bypass the LLM entirely
        result = handle(user_input, store)
        if result is not None:
            print(f"\n{result}\n")
            continue

        # Inject explicit step hint when an issue number is mentioned
        message = user_input
        if match := re.search(r'issue\s*#?(\d+)', user_input, re.IGNORECASE):
            message += (
                f"\n\n[Mandatory first steps: call get_issue({match.group(1)}), "
                f"then search_memory with 2-3 keywords, then list_files to find paths.]"
            )

        # Regular message — send to agent
        response = chat(message, session_id=session_id)
        session_messages.append(("user", user_input))
        session_messages.append(("agent", response))
        print(f"\nagent> {response}\n")


def _close_session(session_id: str, messages: list[tuple[str, str]], store: MemoryStore) -> None:
    end_of_session(session_id, messages, store)
