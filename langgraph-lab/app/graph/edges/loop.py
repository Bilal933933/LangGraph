"""موجه الحلقة (agent ⇄ tools حتى ينتهي استدعاء الأدوات)."""

from typing import Literal

from langchain_core.messages import AIMessage

from app.domain.state import ChatState

LoopTarget = Literal["tools", "end"]


def route_after_agent(state: ChatState) -> LoopTarget:
    """آخر رسالة تحمل tool_calls ← الأدوات، وإلا ← النهاية."""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"
