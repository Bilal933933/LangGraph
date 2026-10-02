"""العقد (Nodes = دوال المعالجة داخل الرسم)."""

import re
from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage

from app.domain.ports import ChatModelPort
from app.domain.state import ChatState, Intent
from app.graph.content import message_text

_GREETINGS = frozenset({"مرحبا", "مرحباً", "سلام", "السلام", "hello", "hi", "hey", "salam"})
_QUESTIONS = frozenset(
    {"ماذا", "كيف", "لماذا", "متى", "أين", "هل", "ما", "what", "how", "why", "when", "where"}
)


def classify_node(state: ChatState) -> dict[str, Intent]:
    """العقدة 1: تصنيف قاعدي بسيط (المرحلة 2).

    greeting = تحية قصيرة → مسار سريع بلا LLM.
    question/chat = الباقي → عقدة answer عبر LLM.
    """
    messages = state.get("messages", [])
    text = message_text(messages[-1].content) if messages else ""
    lowered = text.strip().lower()
    tokens = set(re.findall(r"\w+", lowered, re.UNICODE))
    if "؟" in text or "?" in text or not tokens.isdisjoint(_QUESTIONS):
        return {"intent": "question"}
    if len(lowered) < 30 and not tokens.isdisjoint(_GREETINGS):
        return {"intent": "greeting"}
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
