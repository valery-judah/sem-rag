
# in-gemini

In a custom-built orchestrator, the harness wraps the LLM. In Roo-Code, **the agent is already its own orchestrator** with a built-in ReAct loop and tool permissions. Therefore, we must refactor the harness from being a standalone executable engine into a set of **file-based state machines** and **agent-specific mode configurations** that natively constrain Roo-Code's behavior.