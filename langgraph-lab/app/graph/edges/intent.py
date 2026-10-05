"""موجه النية (classify ← فرع حسب نية المعلم وسياق الجلسة)."""

from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage

from app.core.trace import get_logger
from app.domain.models import AMBIGUOUS_INTENTS
from app.domain.state import ChatState

RouteTarget = Literal["greeting", "answer", "decline", "extract", "plan_extract", "extract_profile"]

#: نوايا غامضة لا تقطع استكمال طلب ناقص (مركزية في domain.models).
_AMBIGUOUS_INTENTS = AMBIGUOUS_INTENTS

#: توجيه مباشر: نية ← عقدة (الخارج عنها ← answer مع تحذير).
_DIRECT_ROUTES: dict[str, RouteTarget] = {
    "generate_quiz": "extract",
    "plan_lesson": "plan_extract",
    "unsupported": "decline",
    "update_profile": "extract_profile",
}


def _resume_incomplete(state: ChatState) -> RouteTarget | None:
    """طلب ناقص + نية غامضة ← عقدة الاستكمال (الخطة أولا عند الازدواج)."""
    if not state.get("missing_fields"):
        return None
    if state.get("intent") not in _AMBIGUOUS_INTENTS:
        return None
    if state.get("lesson_request") is not None:
        return "plan_extract"
    if state.get("quiz_request") is not None:
        return "extract"
    return None


def _has_prior_ai(messages: list[BaseMessage]) -> bool:
    """رسائل الحالة ← True عند وجود أي رد سابق (توقف مبكر)."""
    return any(isinstance(message, AIMessage) for message in messages)


def _route_greeting(state: ChatState) -> RouteTarget | None:
    """نية تحية ← الأولى greeting واللاحقة answer (None لغير التحية)."""
    if state.get("intent") != "greeting":
        return None
    if _has_prior_ai(list(state.get("messages", []))):
        return "answer"
    return "greeting"


def route_by_intent(state: ChatState) -> RouteTarget:
    """نية المعلم + سياق الجلسة ← اسم العقدة التالية.

    التحية الأولى (لا رد سابق في السجل) ← greeting الثابتة.
    تحية لاحقة في نفس thread_id ← answer ليرد النموذج من نافذة
    السياق (Context Window) بدل تكرار الترحيب الأول.
    استكمال طلب ناقص (missing_fields) له أولوية على النية الغامضة
    حتى لا يضيع موضوع الدرس بين الدورين.
    """
    resumed = _resume_incomplete(state)
    if resumed is not None:
        return resumed
    greeted = _route_greeting(state)
    if greeted is not None:
        return greeted
    intent = state.get("intent", "general_question")
    direct = _DIRECT_ROUTES.get(str(intent))
    if direct is not None:
        return direct
    if str(intent) != "general_question":
        get_logger().warning("stage=intent.unknown intent=%s", str(intent))
    return "answer"
