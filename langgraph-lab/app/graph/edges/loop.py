"""موجه الحلقة (agent ⇄ tools حتى ينتهي استدعاء الأدوات)."""

from typing import Literal

from langchain_core.messages import AIMessage

from app.domain.state import ChatState

LoopTarget = Literal["tools", "end"]
QuizLoopTarget = Literal["quiz_tools", "end"]


def route_after_agent(state: ChatState) -> LoopTarget:
    """آخر رسالة تحمل tool_calls ← الأدوات، وإلا ← النهاية (اسم قديم)."""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tools"
    return "end"


def route_after_quiz_agent(state: ChatState) -> QuizLoopTarget:
    """موجه وكيل الاختبارات: tool_calls ← أدواته، وإلا ← النهاية."""
    messages = state.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        return "quiz_tools"
    return "end"
