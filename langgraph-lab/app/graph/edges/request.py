"""موجه الطلب الموحد (Canonical ← فرع حتمي، لا يقرأ النص الطبيعي)."""

from typing import Literal

from langchain_core.messages import AIMessage, BaseMessage

from app.core.trace import get_logger
from app.domain.models import AMBIGUOUS_INTENTS, CanonicalRequest
from app.domain.state import ChatState

RequestTarget = Literal[
    "greeting",
    "answer",
    "decline",
    "extract",
    "worksheet_extract",
    "plan_extract",
    "extract_profile",
]

_AMBIGUOUS = AMBIGUOUS_INTENTS

_DIRECT: dict[str, RequestTarget] = {
    "generate_quiz": "extract",
    "generate_worksheet": "worksheet_extract",
    "plan_lesson": "plan_extract",
    "unsupported": "decline",
    "update_profile": "extract_profile",
}


def _canonical(state: ChatState) -> CanonicalRequest | None:
    raw = state.get("canonical_request")
    return raw if isinstance(raw, CanonicalRequest) else None


def _resume_incomplete(state: ChatState) -> RequestTarget | None:
    """طلب ناقص + نية غامضة ← عقدة الاستكمال السابقة."""
    req = _canonical(state)
    missing = list(req.missing) if req is not None else list(state.get("missing_fields", []))
    if not missing:
        return None
    intent = req.intent if req is not None else str(state.get("intent", ""))
    if intent not in _AMBIGUOUS:
        return None
    if state.get("lesson_request") is not None:
        return "plan_extract"
    if state.get("quiz_request") is not None:
        return "extract"
    if state.get("worksheet_request") is not None:
        return "worksheet_extract"
    # بلا طلب فرعي قديم: الناقص نفسه يحدد الفرع عبر النية الأصلية.
    return None


def _has_prior_ai(messages: list[BaseMessage]) -> bool:
    return any(isinstance(m, AIMessage) for m in messages)


def route_by_request(state: ChatState) -> RequestTarget:
    """طلب موحد ← اسم العقدة التالية (حتمي بالكامل)."""
    resumed = _resume_incomplete(state)
    if resumed is not None:
        return resumed
    req = _canonical(state)
    intent = req.intent if req is not None else str(state.get("intent", "general_question"))
    if intent == "greeting" and not _has_prior_ai(list(state.get("messages", []))):
        return "greeting"
    if intent == "greeting":
        return "answer"
    direct = _DIRECT.get(str(intent))
    if direct is not None:
        return direct
    if str(intent) != "general_question":
        get_logger().warning("stage=request.unknown intent=%s", str(intent))
    return "answer"
