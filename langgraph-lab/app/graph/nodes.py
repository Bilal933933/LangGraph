"""العقد (Nodes = دوال المعالجة داخل الرسم)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.domain.models import QuizRequest
from app.domain.ports import ChatModelPort, StructuredOutputPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.prompts import CLASSIFY_SYSTEM, EXTRACT_SYSTEM

_REQUIRED_LABELS = {
    "topic": "موضوع الدرس",
    "grade_level": "المستوى الدراسي",
    "num_questions": "عدد الأسئلة",
}


def make_classify_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع التصنيف: يغلق على المنفذ المهيكل مع سقوط ناعم."""

    def _classify(state: ChatState) -> dict[str, object]:
        from app.domain.models import IntentResult

        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=CLASSIFY_SYSTEM),
            HumanMessage(content=last),
        ]
        for _ in range(2):
            try:
                result = structured.parse(prompt, IntentResult)
                return {"intent": result.intent}
            except Exception:
                continue
        return {"intent": "general_question"}

    return _classify


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
            req = structured.parse(prompt, QuizRequest)
        except Exception:
            req = QuizRequest()
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


def make_decline_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة الرفض: خارج النطاق ← رسالة ثابتة."""

    def _decline(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="عذرا، هذا خارج نطاق مساعد المعلم.")]}  # noqa: ARG001

    return _decline


def make_greeting_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة التحية: رد ثابت بلا LLM (مسار سريع)."""

    def _greet(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="أهلاً بك! كيف أقدر أساعدك اليوم؟")]}

    return _greet


def make_answer_node(
    model: ChatModelPort,
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع الإجابة: يغلق (Closure) على النموذج المحقون."""

    def _answer(state: ChatState) -> dict[str, list[BaseMessage]]:
        text = model.invoke(list(state["messages"]))
        return {"messages": [AIMessage(content=text)]}

    return _answer
