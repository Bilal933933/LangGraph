"""عقدة التصنيف (النية عبر المخرجات المهيكلة)."""

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.domain.models import DEFAULT_INTENT, IntentResult
from app.domain.ports import StructuredOutputPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.prompts import CLASSIFY_SYSTEM


def make_classify_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع التصنيف: يغلق على المنفذ المهيكل مع سقوط ناعم."""

    def _classify(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        humans: list[str] = []
        for message in reversed(messages):
            if isinstance(message, HumanMessage):
                text = message_text(message.content).strip()
                if text:
                    humans.append(text)
                if len(humans) >= 2:
                    break
        if humans:
            last = " ".join(reversed(humans))[:500]
        elif messages:
            last = message_text(messages[-1].content)
        else:
            last = ""
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
        return {"intent": DEFAULT_INTENT}

    return _classify
