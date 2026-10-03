"""موجه النية (classify ← فرع حسب نية المعلم)."""

from typing import Literal

from app.domain.state import ChatState

RouteTarget = Literal["greeting", "answer", "decline", "extract"]


def route_by_intent(state: ChatState) -> RouteTarget:
    """نية المعلم ← اسم العقدة التالية."""
    intent = state.get("intent", "general_question")
    if intent == "greeting":
        return "greeting"
    if intent == "generate_quiz":
        return "extract"
    if intent == "unsupported":
        return "decline"
    return "answer"
