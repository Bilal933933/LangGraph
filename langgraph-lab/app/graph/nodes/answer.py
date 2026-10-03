"""عقد الردود (تحية وإجابة ورفض)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from app.domain.ports import ChatModelPort
from app.domain.state import ChatState


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
        reply = model.invoke(list(state["messages"]))
        reply.name = "answer"
        return {"messages": [reply]}

    return _answer


def make_decline_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة الرفض: خارج النطاق ← رسالة ثابتة."""

    def _decline(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="عذرا، هذا خارج نطاق مساعد المعلم.")]}  # noqa: ARG001

    return _decline
