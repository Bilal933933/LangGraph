"""منطق التطبيق (Use Case الوحيد)."""

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from app.graph.content import message_text


class ChatService:
    """المنسق الوحيد بين API والرسم. لا يعرف Gemini مباشرة."""

    #: حد خطوات الرسم (حماية الحلقات من التكرار اللانهائي).
    MAX_STEPS = 12

    def __init__(self, graph: Any) -> None:
        self._graph = graph

    def handle_message(self, message: str) -> str:
        """نص الدخل ← نص الرد النهائي."""
        cleaned = message.strip()
        result: dict[str, list[BaseMessage]] = self._graph.invoke(
            {"messages": [HumanMessage(content=cleaned)]},
            {"recursion_limit": self.MAX_STEPS},
        )
        messages = result["messages"]
        last = messages[-1]
        return message_text(last.content)
