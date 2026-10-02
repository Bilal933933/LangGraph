"""دوال التوجيه (Edges = شروط الانتقال بين العقد)."""

from typing import Literal

from app.domain.state import ChatState

RouteTarget = Literal["greeting", "answer", "decline", "extract"]
ExtractTarget = Literal["ask_clarification", "confirm_ready"]


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


def route_after_extract(state: ChatState) -> ExtractTarget:
    """الحقول الناقصة ← استيضاح أو تأكيد الاكتمال."""
    if state.get("missing_fields"):
        return "ask_clarification"
    return "confirm_ready"
