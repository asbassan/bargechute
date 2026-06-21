"""End-of-session hooks.

After each session the agent summarises what happened and stores it
as an episodic memory so future sessions can learn from it.
"""
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from config import MODEL, OLLAMA_BASE_URL
from memory import MemoryStore, EPISODIC, SOURCE_SESSION


def end_of_session(session_id: str, messages: list[tuple[str, str]], store: MemoryStore) -> None:
    """Summarise the session and store as episodic memory.

    messages: list of (role, content) tuples collected during the session.
    Does nothing if the session had fewer than 2 exchanges.
    """
    if len(messages) < 2:
        return

    conversation = "\n".join(f"{role}: {content[:300]}" for role, content in messages)

    prompt = f"""Summarise this Barge coding session in 3-5 bullet points.
Focus on: what was implemented, what errors were hit, what was fixed, what was learned.
Be brief and factual. Use past tense.

Session:
{conversation}"""

    try:
        llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
        response = llm.invoke([HumanMessage(prompt)])
        summary = response.content.strip()
        if store.exists(session_id):
            store.append(session_id, summary, source=SOURCE_SESSION)
            print(f"\n[session summary appended: {session_id}]")
        else:
            store.store(EPISODIC, session_id, summary, source=SOURCE_SESSION, importance=3)
            print(f"\n[session summary stored: {session_id}]")
    except Exception as e:
        print(f"\n[could not store session summary: {e}]")
