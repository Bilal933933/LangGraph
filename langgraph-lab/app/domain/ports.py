"""الواجهات (Protocols = عقود تجريدية لعكس الاعتماد)."""

from typing import Protocol, TypeVar

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel


class ChatModelPort(Protocol):
    """عقد النموذج: أي نموذج (Gemini/وهمي للاختبار) يلتزم به."""

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        """رسائل الدخل ← رسالة النموذج كاملة (قد تحمل tool_calls)."""
        ...

    def bind_tools(self, tools: list[BaseTool]) -> "ChatModelPort":
        """يربط الأدوات ← نموذج قادر على طلب استدعائها."""
        ...


T = TypeVar("T", bound=BaseModel)


class StructuredOutputPort(Protocol):
    """عقد المخرجات المهيكلة: رسائل + نوع ← كائن محقق."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        """رسائل الدخل ونوع Pydantic ← كائن من ذلك النوع."""
        ...


class LessonRepository(Protocol):
    """عقد محتوى الدروس: موضوع ← نص الدرس أو فارغ."""

    def get(self, topic: str) -> str | None:
        """موضوع الدرس ← محتواه أو None عند الغياب."""
        ...
