"""الواجهات (Protocols = عقود تجريدية لعكس الاعتماد)."""

from typing import Protocol, TypeVar

from langchain_core.messages import BaseMessage
from pydantic import BaseModel


class ChatModelPort(Protocol):
    """عقد النموذج: أي نموذج (Gemini/وهمي للاختبار) يلتزم به."""

    def invoke(self, messages: list[BaseMessage]) -> str:
        """رسائل الدخل ← نص الرد."""
        ...


T = TypeVar("T", bound=BaseModel)


class StructuredOutputPort(Protocol):
    """عقد المخرجات المهيكلة: رسائل + نوع ← كائن محقق."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        """رسائل الدخل ونوع Pydantic ← كائن من ذلك النوع."""
        ...
