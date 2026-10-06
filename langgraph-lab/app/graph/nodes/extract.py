"""عقد الاستخراج والاستيضاح والتأكيد (مسار توليد الاختبار)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.domain.models import LessonPlan, QuizRequest
from app.domain.ports import StructuredOutputPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.prompts import EXTRACT_SYSTEM

_REQUIRED_LABELS = {
    "topic": "موضوع الدرس",
    "grade_level": "المستوى الدراسي",
    "num_questions": "عدد الأسئلة",
}


def make_extract_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع الاستخراج: طلب المعلم ← معاملات + نواقص."""

    def _extract(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=EXTRACT_SYSTEM),
            HumanMessage(content=last),
        ]
        try:
            fresh = structured.parse(prompt, QuizRequest)
        except Exception:
            fresh = QuizRequest()
        prev: object = state.get("quiz_request")
        if isinstance(prev, QuizRequest):
            prev_topic, prev_grade = prev.topic, prev.grade_level
            prev_num, prev_types = prev.num_questions, prev.question_types
        elif isinstance(prev, dict):
            prev_topic = str(prev.get("topic") or "") or None
            prev_grade = str(prev.get("grade_level") or "") or None
            raw_num = prev.get("num_questions")
            prev_num = int(raw_num) if isinstance(raw_num, int) else None
            raw_types = prev.get("question_types")
            prev_types = [str(t) for t in raw_types] if isinstance(raw_types, list) else []
        else:
            prev_topic, prev_grade, prev_num, prev_types = None, None, None, []
        topic = fresh.topic or prev_topic
        grade = fresh.grade_level or prev_grade
        num = fresh.num_questions or prev_num
        types = fresh.question_types or prev_types
        # زر (أنشئ اختبارا لهذا الدرس): عند غياب الموضوع في الرسالة
        # نملأ من خطة الدرس الجاهزة في نفس الجلسة بدلا من السؤال مجددا.
        # العدد الافتراضي 5 عند الزر فقط، والمباشر بلا خطة يبقى يسأل.
        has_plan = "plan_draft" in state and state.get("plan_draft") is not None
        draft: object = state.get("plan_draft")
        if (not topic or not grade) and isinstance(draft, LessonPlan):
            plan = draft
            topic = topic or plan.topic
            grade = grade or plan.grade_level
        elif (not topic or not grade) and isinstance(draft, dict):
            raw = draft
            topic = topic or (str(raw.get("topic") or "") or None)
            grade = grade or (str(raw.get("grade_level") or "") or None)
        if has_plan and not num:
            num = 5
        req = QuizRequest(
            topic=topic, grade_level=grade, num_questions=num, question_types=list(types or [])
        )
        missing: list[str] = []
        if not req.topic:
            missing.append("topic")
        if not req.grade_level:
            missing.append("grade_level")
        if not req.num_questions:
            missing.append("num_questions")
        return {"quiz_request": req, "missing_fields": missing}

    return _extract


def ask_clarification_node(state: ChatState) -> dict[str, list[BaseMessage]]:
    """عقدة الاستيضاح: نواقص ← سؤال للمعلم."""
    missing = state.get("missing_fields", [])
    labels = [_REQUIRED_LABELS.get(f, f) for f in missing] or ["التفاصيل"]
    text = "لم تحدد: " + "، ".join(labels) + ". أرسلها لأكمل طلبك."
    return {"messages": [AIMessage(content=text)]}


def confirm_ready_node(state: ChatState) -> dict[str, list[BaseMessage]]:
    """عقدة التأكيد: طلب مكتمل ← رسالة جاهزية (التوليد في المرحلة 3)."""
    req = state.get("quiz_request")
    if req is None:
        return {"messages": [AIMessage(content="طلبك مكتمل وجاهز للتوليد.")]}
    text = (
        f"طلبك مكتمل: {req.num_questions} أسئلة عن {req.topic} "
        f"({req.grade_level}). سأولده في الخطوة التالية."
    )
    return {"messages": [AIMessage(content=text)]}
