"""bargechute — interactive REPL for the Barge coding agent."""
from agent import chat


def main():
    print("bargechute — Barge coding agent")
    print("Type 'exit' to quit, 'new' to start a fresh session.\n")
    session_id = "default"
    session_count = 0

    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            break
        if user_input.lower() == "new":
            session_count += 1
            session_id = f"session_{session_count}"
            print(f"Started new session: {session_id}\n")
            continue

        response = chat(user_input, session_id=session_id)
        print(f"\nagent> {response}\n")


if __name__ == "__main__":
    main()
