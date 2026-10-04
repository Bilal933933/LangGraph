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


class TeacherDirectoryPort(Protocol):
    """عقد أسماء المعلمين: هوية ← اسم للتحية فقط (جلب كسول)."""

    def get_name(self, teacher_id: int) -> str | None:
        """معرف المعلم ← اسمه أو None عند الغياب."""
        ...


class TeacherProfileWriterPort(Protocol):
    """عقد كتابة ملف المعلم: الهوية من الحالة فقط، لا من النموذج."""

    def update_name(self, teacher_id: int, name: str) -> str:
        """يحفظ الاسم المنظف للمعلم ← الاسم المحفوظ."""
        ...


class TeacherProfilePort(Protocol):
    """عقد الملف الكامل: تحميل اللقطة + حفظ الترقيع (الحقول الفارغة فقط).

    اللقطة: {name: str, subject: str, grades: list[str]} والغائب = "" أو [].
    grades تدمج اتحادا لا استبدالا (المعلم يدرس صفوفا متعددة).
    """

    def load_profile(self, teacher_id: int) -> dict[str, object]:
        """الهوية ← اللقطة الكاملة."""
        ...

    def save_profile(self, teacher_id: int, patch: dict[str, object]) -> dict[str, object]:
        """يطبق القيم المنظفة غير الفارغة ← اللقطة الكاملة بعد الحفظ."""
        ...
