"""العقد (Nodes = دوال المعالجة داخل الرسم)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from app.domain.ports import ChatModelPort
from app.domain.state import ChatState
from app.graph.content import message_text


def classify_node(state: ChatState) -> dict[str, str]:
    """العقدة 1: تصنيف قاعدي بسيط (المرحلة 2).

    greeting = تحية قصيرة → مسار سريع بلا LLM.
    question/chat = الباقي → عقدة answer عبر LLM.
    """

    messages = state.get("messages", [])
    text = message_text(messages[-1].content) if messages else ""
    lowered = text.strip().lower()
    greetings = ("مرحبا", "مرحباً", "سلام", "السلام", "hello", "hi", "hey", "salam")
    questions = ("؟", "?", "ماذا", "كيف", "لماذا", "متى", "أين", "هل", "ما ", "what", "how", "why")
    if any(g in lowered for g in greetings) and len(lowered) < 30:
        return {"intent": "greeting"}
    if any(q in lowered for q in questions):
        return {"intent": "question"}
    return {"intent": "chat"}


def make_greeting_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة التحية: رد ثابت بلا LLM (مسار سريع)."""

    def _greet(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="أهلاً بك! كيف أقدر أساعدك اليوم؟")]}

    return _greet


def make_answer_node(
    model: ChatModelPort,
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع العقدة 2: يغلق (Closure) على النموذج المحقون."""

    def _answer(state: ChatState) -> dict[str, list[BaseMessage]]:
        text = model.invoke(list(state["messages"]))
        return {"messages": [AIMessage(content=text)]}

    return _answer
