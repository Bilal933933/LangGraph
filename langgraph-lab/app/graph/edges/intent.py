"""موجه النية (classify ← فرع حسب نية المعلم وسياق الجلسة)."""

from typing import Literal

from langchain_core.messages import AIMessage

from app.domain.state import ChatState

RouteTarget = Literal["greeting", "answer", "decline", "extract", "extract_profile"]


def route_by_intent(state: ChatState) -> RouteTarget:
    """نية المعلم + سياق الجلسة ← اسم العقدة التالية.

    التحية الأولى (لا رد سابق في السجل) ← greeting الثابتة.
    تحية لاحقة في نفس thread_id ← answer ليرد النموذج من نافذة
    السياق (Context Window) بدل تكرار الترحيب الأول.
    """
    intent = state.get("intent", "general_question")
    if intent == "greeting":
        prior_ai = sum(1 for m in state.get("messages", []) if isinstance(m, AIMessage))
        if prior_ai > 0:
            return "answer"
        return "greeting"
    if intent == "generate_quiz":
        return "extract"
    if intent == "unsupported":
        return "decline"
    if intent == "update_profile":
        return "extract_profile"
    return "answer"
