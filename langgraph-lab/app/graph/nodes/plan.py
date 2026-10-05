"""عقد التحضير (مخطط البحث + استرجاع + عمال متوازيون + دمج).

القاعدة: مخطط واحد يحدد ماذا نبحث، واسترجاع واحد مشترك،
ثم عمال Send متوازيون لكل قسم، ثم دمج حتمي واحد.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.types import Send

from app.core.config import get_settings
from app.domain.models import ClarificationOut, LessonPlan, LessonRequest
from app.domain.ports import ChatModelPort, KnowledgeSearchPort, StructuredOutputPort
from app.domain.state import PLAN_SECTION_KINDS, ChatState
from app.graph.content import message_text
from app.graph.nodes.retrieve import (
    build_search_query,
    format_knowledge_context,
    format_sources_block,
)
from app.graph.prompts import PLAN_EXTRACT_SYSTEM, PLAN_REPAIR_SYSTEM, PLAN_SECTION_SYSTEMS
from app.graph.prompts.responses.lesson_plan import render_lesson_plan

_EVASIVE_MARKERS = (
    "زودني",
    "حدد الموضوع",
    "تحديد الموضوع",
    "نسيت تحديد",
    "لم تحدد",
    "غير محدد",
    "في انتظار",
    "أرجو منك",
    "يرجى تزويدي",
    "لم ترفق",
    "لم يتم تحديد",
    "أخبرني بالموضوع",
    "ما هو الموضوع",
    "اكتب اسم المفهوم",
    "بين القوسين",
    "[...",
    "إذا كنت ترغب",
    "يمكنك تعديل",
    "قابلاً للتخصيص",
    "قابلا للتخصيص",
    "نموذجاً افتراضياً",
    "نموذجا افتراضيا",
    "سأقترح نشاطين",
    "في مجال \"تطوير الذات",
    "بصفتي خبير شرح، أنا جاهز",
    "الرجاء تزويدي",
)


def is_evasive(body: str, topic: str = "") -> bool:
    """نص القسم ← True عند التهرب بدل التوليد (سؤال توضيحي/اعتذار/خروج)."""
    text = body.strip()
    if len(text) < 40:
        return True
    if any(marker in text for marker in _EVASIVE_MARKERS):
        return True
    key = topic.strip()
    return bool(key and len(key) >= 2 and key not in text)

_PLAN_REQUIRED_LABELS = {
    "topic": "موضوع الدرس",
    "grade_level": "المستوى الدراسي",
    "minutes": "زمن الحصة",
}


def make_plan_extract_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """طلب المعلم ← LessonRequest + نواقص."""

    def _extract(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=PLAN_EXTRACT_SYSTEM),
            HumanMessage(content=last),
        ]
        try:
            fresh = structured.parse(prompt, LessonRequest)
        except Exception:
            fresh = LessonRequest()
        prev: object = state.get("lesson_request")
        if isinstance(prev, LessonRequest):
            prev_topic, prev_grade, prev_minutes = prev.topic, prev.grade_level, prev.minutes
        elif isinstance(prev, dict):
            prev_topic = str(prev.get("topic") or "") or None
            prev_grade = str(prev.get("grade_level") or "") or None
            raw_minutes = prev.get("minutes")
            prev_minutes = int(raw_minutes) if isinstance(raw_minutes, int) else None
        else:
            prev_topic, prev_grade, prev_minutes = None, None, None
        topic = fresh.topic or prev_topic
        grade = fresh.grade_level or prev_grade
        minutes = fresh.minutes or prev_minutes
        req = LessonRequest(topic=topic, grade_level=grade, minutes=minutes)
        missing: list[str] = []
        if not req.topic:
            missing.append("topic")
        if not req.grade_level:
            missing.append("grade_level")
        if not req.minutes:
            missing.append("minutes")
        return {"lesson_request": req, "missing_fields": missing}

    return _extract


def make_plan_retrieve_node(
    knowledge: KnowledgeSearchPort | None = None,
    limit: int | None = None,
) -> Callable[[ChatState], dict[str, object]]:
    """LessonRequest ← مصادر مشتركة لكل العمال (بحث واحد فقط)."""

    def _retrieve(state: ChatState) -> dict[str, object]:
        req: object = state.get("lesson_request")
        if isinstance(req, LessonRequest):
            topic = req.topic or ""
        elif isinstance(req, dict):
            topic = str(req.get("topic") or "")
        else:
            topic = ""
        # البحث بالموضوع فقط: كلمات الصف/الزمن تحصر النتائج في الكتاب
        # المدرسي وتحجب الكتب المرجعية (الصف يبقى في الحالة للتدريس).
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


def plan_dispatch(state: ChatState) -> list[Send]:
    """موزع Send: طلب جاهز ← عامل متوازي لكل قسم بنفس المصادر."""
    return [Send("plan_section", {"section_task": kind}) for kind in PLAN_SECTION_KINDS]


def make_plan_section_node(
    model: ChatModelPort,
    limit: int | None = None,
) -> Callable[[ChatState], dict[str, object]]:
    """عامل قسم واحد: (طلب + مصادر + نوع القسم) ← قسم مهيكل."""

    def _section(state: ChatState) -> dict[str, object]:
        kind = state.get("section_task") or "objectives"
        system = PLAN_SECTION_SYSTEMS.get(str(kind), PLAN_SECTION_SYSTEMS["objectives"])
        req: object = state.get("lesson_request")
        if isinstance(req, LessonRequest):
            topic, grade, minutes = req.topic or "", req.grade_level or "", req.minutes or 45
        elif isinstance(req, dict):
            topic = str(req.get("topic") or "")
            grade = str(req.get("grade_level") or "")
            raw = req.get("minutes")
            minutes = int(raw) if isinstance(raw, int) else 45
        else:
            topic, grade, minutes = "", "", 45
        chunks = state.get("retrieved_sources", [])
        eff = limit if limit is not None else get_settings().plan_retrieval_limit
        context = format_knowledge_context(list(chunks or []), limit=eff)
        anchored = (
            f"{system}\nموضوع هذه المهمة حصراً: {topic} ({grade}). "
            "كل جملة تكتبها يجب أن تكون عن هذا الموضوع، واذكر اسمه صراحة "
            "في كل فقرة."
        )
        prompt: list[BaseMessage] = [SystemMessage(content=anchored)]
        if context is not None:
            prompt.append(SystemMessage(content=context))
        prompt.append(
            HumanMessage(
                content=(
                    f"اكتب قسم {kind} لدرس {topic} للصف {grade} "
                    f"(الحصة {minutes} دقيقة) من المصادر أعلاه."
                )
            )
        )
        reply = model.invoke(prompt)
        body = message_text(reply.content).strip() or "تعذر التوليد من المصادر."
        section = {"kind": str(kind), "title": str(kind), "body": body}
        return {"plan_sections": [section]}

    return _section


def make_plan_clarification_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """نواقص التحضير ← سؤال للمعلم."""

    def _ask(state: ChatState) -> dict[str, list[BaseMessage]]:
        missing = state.get("missing_fields", [])
        labels = [_PLAN_REQUIRED_LABELS.get(f, f) for f in missing] or ["التفاصيل"]
        text = "لتحضير الدرس أحتاج: " + "، ".join(labels) + "."
        return {"messages": [AIMessage(content=text)]}

    return _ask


#: اقتراحات عامة للصف عند فراغ ملف المعلم.
_GENERAL_GRADES = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس", "السادس"]


def build_plan_clarification(state: ChatState) -> ClarificationOut | None:
    """نواقص التحضير + لقطة الملف ← مهيكل الديلوج أو None عند الاكتمال."""
    missing = [str(f) for f in state.get("missing_fields", []) if str(f).strip()]
    if not missing:
        return None
    snapshot = state.get("profile_snapshot")
    grades: list[str] = []
    if isinstance(snapshot, dict):
        raw = snapshot.get("grades")
        if isinstance(raw, list):
            grades = [str(g).strip() for g in raw if str(g).strip()]
    suggestions: dict[str, list[str]] = {}
    if "minutes" in missing:
        suggestions["minutes"] = ["30", "45", "60"]
    if "grade_level" in missing:
        suggestions["grade_level"] = grades or list(_GENERAL_GRADES)
    if "topic" in missing:
        suggestions["topic"] = []
    name_empty = not (isinstance(snapshot, dict) and str(snapshot.get("name") or "").strip())
    subject_empty = not (isinstance(snapshot, dict) and str(snapshot.get("subject") or "").strip())
    return ClarificationOut(
        kind="plan",
        missing=missing,
        suggestions=suggestions,
        profile_empty=bool(name_empty and subject_empty and not grades),
    )


def make_plan_merge_node(
    model: ChatModelPort | None = None,
    limit: int | None = None,
) -> Callable[[ChatState], dict[str, object]]:
    """دمج حتمي: أقسام العمال ← LessonPlan + رسالة نهائية واحدة.

    بوابة الجودة: أي قسم متهرب يعاد توليده مرة واحدة ببرومبت الإصلاح،
    فيبقى عدد الاستدعاءات محدوداً ولا حلقة لانهائية.
    """

    def _merge(state: ChatState) -> dict[str, object]:
        req: object = state.get("lesson_request")
        if isinstance(req, LessonRequest):
            topic, grade, minutes = req.topic or "الدرس", req.grade_level or "", req.minutes or 45
        elif isinstance(req, dict):
            topic = str(req.get("topic") or "الدرس")
            grade = str(req.get("grade_level") or "")
            raw = req.get("minutes")
            minutes = int(raw) if isinstance(raw, int) else 45
        else:
            topic, grade, minutes = "الدرس", "", 45
        sections = {str(s.get("kind")): str(s.get("body")) for s in state.get("plan_sections", [])}
        eff = limit if limit is not None else get_settings().plan_retrieval_limit
        if model is not None:
            chunks = state.get("retrieved_sources", [])
            context = format_knowledge_context(list(chunks or []), limit=eff)
            for kind in PLAN_SECTION_KINDS:
                body = sections.get(kind, "")
                if body and not is_evasive(body, topic):
                    continue
                anchored = (
                    f"{PLAN_REPAIR_SYSTEM}\nموضوع هذه المهمة حصراً: {topic} "
                    f"({grade}). كل جملة تكتبها يجب أن تكون عن هذا الموضوع، "
                    "واذكر اسمه صراحة في كل فقرة."
                )
                prompt: list[BaseMessage] = [SystemMessage(content=anchored)]
                if context is not None:
                    prompt.append(SystemMessage(content=context))
                prompt.append(
                    HumanMessage(
                        content=(
                            f"اكتب قسم {kind} لدرس {topic} للصف {grade} "
                            f"(الحصة {minutes} دقيقة) من المصادر أعلاه."
                        )
                    )
                )
                try:
                    fixed = message_text(model.invoke(prompt).content).strip()
                except Exception:
                    fixed = ""
                if fixed and not is_evasive(fixed, topic):
                    sections[kind] = fixed
        plan = LessonPlan(
            topic=topic,
            grade_level=grade or "غير محدد",
            minutes=int(minutes),
            objectives=sections.get("objectives", ""),
            intro=sections.get("intro", ""),
            steps=sections.get("steps", ""),
            activities=sections.get("activities", ""),
            assessment=sections.get("assessment", ""),
        )
        block = format_sources_block(
            list(state.get("retrieved_sources", []) or []), limit=eff
        )
        text = render_lesson_plan(plan, block)
        text = f"{text}\n\n---\nلإنشاء اختبار لهذا الدرس أرسل: أنشئ اختبارا لهذا الدرس (5 أسئلة افتراضا)."
        return {"plan_draft": plan, "messages": [AIMessage(content=text)]}

    return _merge
