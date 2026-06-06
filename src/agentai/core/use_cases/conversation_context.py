"""Helpers for multi-turn compliance conversations."""

from typing import Any, List


def format_conversation_for_llm(prompt_query: str, history: List[dict[str, Any]]) -> str:
    """Build an LLM prompt that includes prior turns plus the latest operator message."""
    if not history:
        return prompt_query

    recent = history[-8:]
    lines = ["Previous conversation:"]
    for turn in recent:
        role = str(turn.get("role", "user")).strip().title()
        content = str(turn.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")

    lines.append(f"\nLatest operator message: {prompt_query}")
    lines.append(
        "Use the conversation context to resolve references like 'this account', 'that patient', or 'their policy'. "
        "Ground the answer in the retrieved MCP data for the latest message."
    )
    return "\n".join(lines)


def format_conversation_for_mcp(prompt_query: str, history: List[dict[str, Any]]) -> str:
    """Merge prior user turns so MCP ID extractors can resolve follow-up questions."""
    if not history:
        return prompt_query

    user_parts = [
        str(turn.get("content", "")).strip()
        for turn in history
        if turn.get("role") == "user" and str(turn.get("content", "")).strip()
    ]
    user_parts.append(prompt_query.strip())
    return " ".join(part for part in user_parts if part)
