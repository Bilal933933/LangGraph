"""عقدتا Parser وValidator (الطلب الموحد هو مركز التوجيه).

parse_request: رسالة + طلب سابق ← LLM مهيكل ← CanonicalRequest.
validate_request: كود حتمي فقط (صلاحية + توافق + نواقص + Revision).
"""

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.domain.models import (
    AMBIGUOUS_INTENTS,
    DEFAULT_INTENT,
    INTENT_VALUES,
    CanonicalRequest,
    IntentResult,
)
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.prompts import PARSER_SYSTEM


def _coerce_prev(raw: object) -> CanonicalRequest | None:
    """لقطة سابقة (كائن أو قاموس) ← CanonicalRequest أو None."""
    if isinstance(raw, CanonicalRequest):
        return raw
    if isinstance(raw, dict):
        try:
            return CanonicalRequest(
                intent=raw.get("intent", DEFAULT_INTENT),
                task=raw.get("task"),
                subject=raw.get("subject"),
                grade_level=raw.get("grade_level"),
                topic=raw.get("topic"),
                missing=list(raw.get("missing") or []),
                parent_request_id=raw.get("parent_request_id"),
            )
        except Exception:
            return None
    return None


def make_parse_request_node(
    structured: object,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع المحلل: آخر رسالة + السابق ← طلب موحد مدمج (Revision)."""

    def _parse(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prev = _coerce_prev(state.get("canonical_request"))
        context = ""
        if prev is not None:
            context = (
                f" الطلب السابق: intent={prev.intent} task={prev.task or ''}"
                f" topic={prev.topic or ''} grade={prev.grade_level or ''}."
            )
        prompt: list[BaseMessage] = [
            SystemMessage(content=PARSER_SYSTEM),
            HumanMessage(content=(last + context)[:800]),
        ]
        parse = getattr(structured, "parse", None)
        fresh: CanonicalRequest | None = None
        if callable(parse):
            for _ in range(2):
                try:
                    fresh = parse(prompt, CanonicalRequest)
                    break
                except Exception:
                    continue
        if fresh is None and callable(parse):
            # توافق خلفي: نماذج الاختبارات الوهمية تعرف IntentResult فقط.
            for _ in range(2):
                try:
                    legacy = parse(prompt, IntentResult)
                    fresh = CanonicalRequest(intent=legacy.intent)
                    break
                except Exception:
                    continue
        if fresh is None:
            fresh = CanonicalRequest(intent=DEFAULT_INTENT)
        # دمج Revision: الفارغ الجديد يرث من السابق (لا مهمة جديدة دائما).
        if prev is not None and fresh.intent in (*AMBIGUOUS_INTENTS, prev.intent):
            merged = CanonicalRequest(
                intent=prev.intent,
                task=fresh.task or prev.task,
                subject=fresh.subject or prev.subject,
                grade_level=fresh.grade_level or prev.grade_level,
                topic=fresh.topic or prev.topic,
                missing=list(fresh.missing or prev.missing),
                parent_request_id="prev",
            )
            return {
                "canonical_request": merged,
                "intent": merged.intent,
                "missing_fields": list(merged.missing),
            }
        return {
            "canonical_request": fresh,
            "intent": fresh.intent,
            "missing_fields": list(fresh.missing),
        }

    return _parse


def validate_request_node(state: ChatState) -> dict[str, object]:
    """مدقق حتمي: صلاحية + نواقص (topic/grade فقط للتوجيه)."""
    raw = _coerce_prev(state.get("canonical_request"))
    if raw is None:
        raw = CanonicalRequest(intent=state.get("intent", DEFAULT_INTENT))
    intent = raw.intent if raw.intent in INTENT_VALUES else DEFAULT_INTENT
    missing: list[str] = []
    if intent in ("plan_lesson", "generate_quiz", "generate_worksheet"):
        if not (raw.topic or "").strip():
            missing.append("topic")
        if not (raw.grade_level or "").strip():
            missing.append("grade_level")
    fixed = CanonicalRequest(
        intent=intent,
        task=raw.task,
        subject=raw.subject,
        grade_level=raw.grade_level,
        topic=raw.topic,
        missing=missing,
        parent_request_id=raw.parent_request_id,
    )
    return {
        "canonical_request": fixed,
        "intent": fixed.intent,
        "missing_fields": missing,
    }
