import sqlite3
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.sqlite import SqliteSaver

from config import DB_PATH, MODEL, OLLAMA_BASE_URL
from tools import TOOLS

SYSTEM_PROMPT = """You are bargechute — an autonomous coding agent specialized in the Barge \
Windows container runtime.

Barge is written in Go. Your job is to:
1. Search memory for relevant knowledge before writing any code
2. Read existing Barge source files to understand context
3. Write or modify Go files to implement the requirement
4. Run go build and go test — iterate until both pass
5. Store what you learned for future sessions

Always search memory first. Always build and test after every change.
"""


def _build_graph(checkpointer):
    llm = ChatOllama(model=MODEL, base_url=OLLAMA_BASE_URL)
    llm_with_tools = llm.bind_tools(TOOLS)

    def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(SYSTEM_PROMPT)] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.set_entry_point("agent")
    builder.add_conditional_edges("agent", tools_condition)
    builder.add_edge("tools", "agent")
    return builder.compile(checkpointer=checkpointer)


DB_PATH.parent.mkdir(parents=True, exist_ok=True)
_conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
_checkpointer = SqliteSaver(_conn)
_graph = _build_graph(_checkpointer)


def chat(message: str, session_id: str = "default") -> str:
    config = {"configurable": {"thread_id": session_id}}
    result = _graph.invoke(
        {"messages": [HumanMessage(message)]},
        config=config,
    )
    return result["messages"][-1].content
