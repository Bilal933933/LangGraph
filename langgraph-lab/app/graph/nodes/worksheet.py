"""عقد ورقة العمل والنشاط (استخراج + استيضاح + استرجاع + كتابة).

القاعدة: تحويل نصي صرف بلا أدوات خارجية — عقدة كتابة واحدة
تستدعي النموذج مباشرة (لا حلقة وكيل)، على نمط مسار الاختبار.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.core.config import get_settings
from app.domain.models import LessonPlan, WorksheetRequest
from app.domain.outputs.worksheet import WorksheetOutput
from app.domain.ports import ChatModelPort, KnowledgeSearchPort, StructuredOutputPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.retrieve import build_search_query, format_knowledge_context
from app.graph.nodes.structured_retry import parse_with_retry
from app.graph.nodes.worksheet_bridge import build_worksheet_shape_prompt
from app.graph.progress import emit as emit_progress
from app.graph.prompts import WORKSHEET_EXTRACT_SYSTEM
from app.rendering.registry import render_for_intent
from app.rendering.worksheet_paper import render_worksheet_paper

_WORKSHEET_REQUIRED_LABELS = {
    "topic": "موضوع الدرس",
    "grade_level": "المستوى الدراسي",
}


def _coerce_request(raw: object) -> WorksheetRequest | None:
    """لقطة طلب (كائن أو قاموس بعد التسلسل) ← WorksheetRequest أو None."""
    if isinstance(raw, WorksheetRequest):
        return raw
    if isinstance(raw, dict):
        try:
            return WorksheetRequest(
                kind=raw.get("kind"),
                topic=raw.get("topic"),
                grade_level=raw.get("grade_level"),
                num_items=raw.get("num_items"),
                minutes=raw.get("minutes"),
            )
        except Exception:
            return None
    return None


def make_worksheet_extract_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع الاستخراج: طلب المعلم ← معاملات + نواقص (اندماج مع السابق)."""

    def _extract(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=WORKSHEET_EXTRACT_SYSTEM),
            HumanMessage(content=last),
        ]
        try:
            fresh = structured.parse(prompt, WorksheetRequest)
        except Exception:
            fresh = WorksheetRequest()
        # محول مؤقت: Canonical أولا عند وجوده.
        canon = state.get("canonical_request")
        canon_topic = getattr(canon, "topic", None)
        canon_grade = getattr(canon, "grade_level", None)
        if isinstance(canon, dict):
            canon_topic = canon.get("topic") or canon_topic
            canon_grade = canon.get("grade_level") or canon_grade
        if isinstance(canon_topic, str) and canon_topic.strip():
            fresh = WorksheetRequest(
                kind=fresh.kind,
                topic=canon_topic.strip(),
                grade_level=fresh.grade_level,
                num_items=fresh.num_items,
                minutes=fresh.minutes,
            )
        if isinstance(canon_grade, str) and canon_grade.strip():
            fresh = WorksheetRequest(
                kind=fresh.kind,
                topic=fresh.topic,
                grade_level=canon_grade.strip(),
                num_items=fresh.num_items,
                minutes=fresh.minutes,
            )
        prev = _coerce_request(state.get("worksheet_request"))
        kind = fresh.kind or (prev.kind if prev else None) or "worksheet"
        topic = fresh.topic or (prev.topic if prev else None)
        grade = fresh.grade_level or (prev.grade_level if prev else None)
        num = fresh.num_items or (prev.num_items if prev else None)
        minutes = fresh.minutes or (prev.minutes if prev else None)
        # زر (ورقة عمل لهذا الدرس): عند غياب الموضوع نملأ من خطة
        # الدرس الجاهزة في نفس الجلسة بدلا من السؤال مجددا.
        draft: object = state.get("plan_draft")
        if isinstance(draft, LessonPlan):
            topic = topic or draft.topic
            grade = grade or draft.grade_level
        elif isinstance(draft, dict):
            topic = topic or (str(draft.get("topic") or "") or None)
            grade = grade or (str(draft.get("grade_level") or "") or None)
        req = WorksheetRequest(
            kind=kind, topic=topic, grade_level=grade, num_items=num, minutes=minutes
        )
        missing: list[str] = []
        if not req.topic:
            missing.append("topic")
        if not req.grade_level:
            missing.append("grade_level")
        return {"worksheet_request": req, "missing_fields": missing}

    return _extract


def make_worksheet_ask_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """نواقص ورقة العمل ← سؤال للمعلم (حتمية بلا نموذج)."""

    def _ask(state: ChatState) -> dict[str, list[BaseMessage]]:
        missing = state.get("missing_fields", [])
        labels = [_WORKSHEET_REQUIRED_LABELS.get(f, f) for f in missing] or ["التفاصيل"]
        text = "لورقة العمل أحتاج: " + "، ".join(labels) + "."
        return {"messages": [AIMessage(content=text)]}

    return _ask


def make_worksheet_retrieve_node(
    knowledge: KnowledgeSearchPort | None = None,
    limit: int | None = None,
) -> Callable[[ChatState], dict[str, object]]:
    """WorksheetRequest ← مصادر مشتركة لعقدة الكتابة (بحث واحد فقط)."""

    def _retrieve(state: ChatState) -> dict[str, object]:
        req = _coerce_request(state.get("worksheet_request"))
        topic = req.topic if req and req.topic else ""
        query = topic.strip() or build_search_query(list(state.get("messages", [])))
        eff = limit if limit is not None else get_settings().plan_retrieval_limit
        chunks: list[dict[str, object]] = []
        if knowledge is not None and query:
            try:
                hybrid = getattr(knowledge, "search_hybrid", None)
                if callable(hybrid):
                    chunks = hybrid(query, eff)
                else:
                    chunks = knowledge.search(query, eff)
            except Exception:
                chunks = []
        sources = [
            {
                "title": str(c.get("title") or "").strip(),
                "subject": str(c.get("subject") or "").strip(),
                "lesson": str(c.get("lesson") or "").strip(),
                "text": str(c.get("text") or "").strip()[:1500],
            }
            for c in chunks[:eff]
            if str(c.get("text") or "").strip()
        ]
        return {"retrieved_sources": sources}

    return _retrieve


def make_worksheet_write_node(
    model: ChatModelPort,
    limit: int | None = None,
    structured: StructuredOutputPort | None = None,
) -> Callable[..., dict[str, object]]:
    """طلب + مصادر ← ورقة عمل نهائية بقالب ثابت (تمرير callbacks للعداد).

    مع structured ← توليد مهيكل + حفظ worksheet_draft + رد نسخة الطالب.
    بدونه ← مسار النص الحر القديم (توافق خلفي).
    """

    def _write(
        state: ChatState, config: RunnableConfig | None = None
    ) -> dict[str, object]:
        emit_progress("worksheet_write", "start")
        req = _coerce_request(state.get("worksheet_request"))
        shape = build_worksheet_shape_prompt(req)
        chunks = state.get("retrieved_sources", [])
        eff = limit if limit is not None else get_settings().plan_retrieval_limit
        context = format_knowledge_context(list(chunks or []), limit=eff)
        topic = req.topic if req and req.topic else ""
        grade = req.grade_level if req and req.grade_level else ""
        prompt: list[BaseMessage] = [SystemMessage(content=shape)]
        if context is not None:
            prompt.append(SystemMessage(content=context))
        prompt.append(HumanMessage(content=f"أنشئ ورقة العمل عن: {topic} ({grade})"))
        if structured is not None:
            emit_progress("worksheet_write", "shaping")
            sheet = parse_with_retry(structured, prompt, WorksheetOutput, what="ورقة عمل")
            paper = render_for_intent("generate_worksheet", sheet)
            out = AIMessage(content=paper)
            out.name = "worksheet_write"
            return {"messages": [out], "worksheet_draft": sheet}
        reply = model.invoke(
            prompt, callbacks=config.get("callbacks") if config is not None else None
        )
        paper = render_worksheet_paper(req, message_text(reply.content))
        out = AIMessage(content=paper)
        out.name = "worksheet_write"
        return {"messages": [out]}

    return _write
