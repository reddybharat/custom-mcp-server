"""Extract MCP tool-call activity from LangChain agent message history."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


def _message_text(msg: object) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    return str(content)


def extract_turn_trace(
    messages: list[Any],
    *,
    context_extra: str | None = None,
) -> dict[str, Any]:
    """Build a trace for the latest agent turn (after the last human message)."""
    last_human_idx = -1
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            last_human_idx = i
            break

    turn_messages = messages[last_human_idx + 1 :] if last_human_idx >= 0 else messages
    steps: list[dict[str, Any]] = []

    for msg in turn_messages:
        if isinstance(msg, AIMessage):
            for tc in msg.tool_calls or []:
                steps.append(
                    {
                        "kind": "tool_call",
                        "name": tc.get("name"),
                        "args": tc.get("args"),
                        "id": tc.get("id"),
                    }
                )
        elif isinstance(msg, ToolMessage):
            steps.append(
                {
                    "kind": "tool_result",
                    "name": getattr(msg, "name", None),
                    "tool_call_id": getattr(msg, "tool_call_id", None),
                    "content": _message_text(msg),
                }
            )

    return {
        "context_injected": context_extra,
        "steps": steps,
    }
