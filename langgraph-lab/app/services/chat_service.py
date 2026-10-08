"""منطق التطبيق (Use Case الوحيد)."""

import hashlib
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from app.core.usage import UsageCollector, record_usage
from app.graph.content import message_text
from app.graph.nodes.plan import build_plan_clarification
from app.graph.streaming import stream_run


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
        """(المالك، المحادثة) ← thread_id. الصيغة ثابتة وقصيرة (<255 حرفًا).

        العلاقة: Conversation (سجل دائم) ← thread (تنفيذ) ← Checkpoint.
        Message DB للعرض فقط ولا يُحقن في Graph.
        """
        return f"t{user_id}:c{conversation_id}"

    @staticmethod
    def parse_thread_id(thread_id: str) -> tuple[int | None, int | None]:
        """thread_id ← (user_id, conversation_id) أو (None, None) عند الشكل الغريب."""
        try:
            user_part, conv_part = thread_id.strip().split(":")
            return int(user_part[1:]), int(conv_part[1:])
        except Exception:
            return None, None

    @staticmethod
    def guest_thread_id(client_ip: str, raw_thread_id: str) -> str:
        """خيط الضيف ← نطاق معزول لكل IP (best-effort لا أمني).

        المسار المسجل يشتق `t{user}:c{conv}` بعد فحص الملكية.
        مسار الضيف بلا هوية: `request.client.host` غير موثوق خلف
        proxy (قد يتساوى للجميع) — العزل هنا ضد التصادم العرضي فقط.
        البصمة `sha256(ip|raw)` تمنع تصادم القص، والطول ≤64 لحد Schema.
        """
        raw = (raw_thread_id or "").strip() or "default"
        ip = (client_ip or "").strip() or "unknown"
        digest = hashlib.sha256(f"{ip}\n{raw}".encode("utf-8")).hexdigest()[:12]
        safe_ip = ip.replace(":", "-")[:32]
        return f"g:{safe_ip}:{digest}"[:64]

    def handle_message(
        self, message: str, thread_id: str = "default", teacher_id: int | None = None
    ) -> str:
        """نص الدخل ← نص الرد النهائي. thread_id يعزل محادثة عن أخرى.

        غلاف متزامن للاختبارات والسكربتات (بلا حلقة حدث).
        داخل نقاط API غير المتزامنة استخدم `handle_message_detail` مباشرة.
        teacher_id هوية داخلية من الطبقة الخارجية (لاحقا من المصادقة)،
        وليست من جسم الطلب. None = ضيف بدون هوية.
        """
        import asyncio

        reply = asyncio.run(
            self.handle_message_detail(message, thread_id, teacher_id)
        )["reply"]
        assert isinstance(reply, str)
        return reply

    async def handle_message_detail(
        self,
        message: str,
        thread_id: str = "default",
        teacher_id: int | None = None,
        session: Session | None = None,
        usage_subject: str | None = None,
    ) -> dict[str, object]:
        """نص الدخل ← {reply, sources, clarification} للديلوج عند النواقص."""
        payload, config = self._run_args(message, thread_id, teacher_id)
        collector: UsageCollector | None = None
        if session is not None and usage_subject is not None:
            collector = UsageCollector()
            config = {**config, "callbacks": [collector]}
        result = await self._graph.ainvoke(payload, config)
        assert isinstance(result, dict)
        detail = self._detail_from_state(result)
        if collector is not None and session is not None and usage_subject is not None:
            record_usage(session, usage_subject, collector.input_tokens, collector.output_tokens)
        return detail

    async def stream_message_detail(
        self,
        message: str,
        thread_id: str = "default",
        teacher_id: int | None = None,
        session: Session | None = None,
        usage_subject: str | None = None,
    ) -> AsyncIterator[dict[str, object]]:
        """يبث stage/token ثم done بالتفصيل الكامل (نفس شكل handle_message_detail)."""
        payload, config = self._run_args(message, thread_id, teacher_id)
        collector: UsageCollector | None = None
        if session is not None and usage_subject is not None:
            collector = UsageCollector()
            config = {**config, "callbacks": [collector]}
        async for event in stream_run(self._graph, payload, config):
            if event.get("type") == "done":
                state = event.get("state")
                assert isinstance(state, dict)
                if (
                    collector is not None
                    and session is not None
                    and usage_subject is not None
                ):
                    record_usage(
                        session, usage_subject, collector.input_tokens, collector.output_tokens
                    )
                yield {"type": "done", **self._detail_from_state(state)}
            else:
                yield event

    def _run_args(
        self, message: str, thread_id: str, teacher_id: int | None
    ) -> tuple[dict[str, object], dict[str, object]]:
        """مدخلات مشتركة للمسارين المتزامن والمتدفق."""
        cleaned = message.strip()
        thread = thread_id.strip() or "default"
        payload: dict[str, object] = {"messages": [HumanMessage(content=cleaned)]}
        if teacher_id is not None:
            payload["teacher_id"] = teacher_id
        config: dict[str, object] = {
            "configurable": {"thread_id": thread},
            "recursion_limit": self.MAX_STEPS,
        }
        return payload, config

    def _detail_from_state(self, result: dict[str, object]) -> dict[str, object]:
        """حالة نهائية ← {reply, sources, clarification}."""
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
