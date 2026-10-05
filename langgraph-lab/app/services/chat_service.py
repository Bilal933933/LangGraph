"""منطق التطبيق (Use Case الوحيد)."""

from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from app.graph.content import message_text
from app.graph.nodes.plan import build_plan_clarification


class ChatService:
    """المنسق الوحيد بين API والرسم. لا يعرف Gemini مباشرة.

    حد التكامل: مصدر الاستمرارية هو Checkpointer عبر thread_id فقط.
    جدول Message للعرض والقوائم والبحث، ولا يُعاد حقنه في الرسم
    وإلا تضاعفت الرسائل مع reducer ‏add_messages.
    """

    #: حد خطوات الرسم (حماية الحلقات من التكرار اللانهائي).
    MAX_STEPS = 12

    def __init__(self, graph: Any) -> None:
        self._graph = graph

    @staticmethod
    def thread_id_for_conversation(user_id: int, conversation_id: int) -> str:
        """(المالك، المحادثة) ← thread_id. الصيغة ثابتة وقصيرة (<255 حرفًا)."""
        return f"t{user_id}:c{conversation_id}"

    def handle_message(
        self, message: str, thread_id: str = "default", teacher_id: int | None = None
    ) -> str:
        """نص الدخل ← نص الرد النهائي. thread_id يعزل محادثة عن أخرى.

        teacher_id هوية داخلية من الطبقة الخارجية (لاحقا من المصادقة)،
        وليست من جسم الطلب. None = ضيف بدون هوية.
        """
        reply = self.handle_message_detail(message, thread_id, teacher_id)["reply"]
        assert isinstance(reply, str)
        return reply

    def handle_message_detail(
        self, message: str, thread_id: str = "default", teacher_id: int | None = None
    ) -> dict[str, object]:
        """نص الدخل ← {reply, sources, clarification} للديلوج عند النواقص."""
        cleaned = message.strip()
        thread = thread_id.strip() or "default"
        payload: dict[str, object] = {"messages": [HumanMessage(content=cleaned)]}
        if teacher_id is not None:
            payload["teacher_id"] = teacher_id
        result: dict[str, object] = self._graph.invoke(
            payload,
            {"configurable": {"thread_id": thread}, "recursion_limit": self.MAX_STEPS},
        )
        messages = result["messages"]
        assert isinstance(messages, list)
        last = messages[-1]
        assert isinstance(last, BaseMessage)
        sources = result.get("retrieved_sources", [])
        assert isinstance(sources, list)
        clarification = build_plan_clarification(result)  # type: ignore[arg-type]
        return {
            "reply": message_text(last.content),
            "sources": sources,
            "clarification": clarification.model_dump() if clarification is not None else None,
        }
