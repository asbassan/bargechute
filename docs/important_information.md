# Important Design Decisions

Notes on non-obvious decisions that should not be undone without understanding the reasoning.

## System prompt does not describe tools

The agent's system prompt (`agent.py: SYSTEM_PROMPT`) deliberately does not list or describe individual tools. Tool descriptions are passed to the LLM via `llm.bind_tools(TOOLS)` — LangChain serialises each tool's name, description, and parameter schema into the model's context automatically.

Duplicating tool descriptions in the system prompt would:
- Add noise that competes with the actual tool schemas
- Create drift risk when a tool description changes (two places to update)
- Waste context window budget on a 7B model

The system prompt covers *workflow and rules* only. Tool-level detail lives in each `@tool` docstring in `tools.py`.
