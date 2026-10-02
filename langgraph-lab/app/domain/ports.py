"""الواجهات (Protocols = عقود تجريدية لعكس الاعتماد)."""

from typing import Protocol

from langchain_core.messages import BaseMessage


class ChatModelPort(Protocol):
    """عقد النموذج: أي نموذج (Gemini/وهمي للاختبار) يلتزم به."""

    def invoke(self, messages: list[BaseMessage]) -> str:
        """رسائل الدخل ← نص الرد."""
        ...
