"""الواجهات (Protocols = عقود تجريدية لعكس الاعتماد)."""

from collections.abc import AsyncIterator
from typing import Any, Protocol, TypeVar

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel


class ChatModelPort(Protocol):
    """عقد النموذج: أي نموذج (Gemini/وهمي للاختبار) يلتزم به."""

    def invoke(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AIMessage:
        """رسائل الدخل ← رسالة النموذج كاملة (قد تحمل tool_calls)."""
        ...

    def bind_tools(self, tools: list[BaseTool]) -> "ChatModelPort":
        """يربط الأدوات ← نموذج قادر على طلب استدعائها."""
        ...

    def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        """بث تدريجي لنص الرد؛ callbacks تُمرر ليلتقطها وضع messages."""
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


class KnowledgeSearchPort(Protocol):
    """عقد البحث المعرفي: سؤال ← مقاطع مرتبة (نصي، أو هجين عند توفر التضمين)."""

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← قائمة {title, text, subject, lesson} الأعلى صلة."""
        ...

    def search_hybrid(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← مقاطع مدمجة دلالي+نصي (يسقط للنصي عند تعذر التضمين)."""
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


class WebSearchPort(Protocol):
    """عقد بحث الويب (قدرة لاحقة، ليست Core).

    الشكل موحد مع RAG: {title, text, url} ليسهل الدمج والعرض.
    """

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← نتائج {title, text, url} الأعلى صلة."""
        ...


class KnowledgeSourcePort(Protocol):
    """عقد القراءة الدقيقة: معرف مقطع ظهر في search ← نصه الكامل.

    القيد: الأداة لا تقبل مسارًا حرًا أبدًا، بل id صحيح موجب فقط.
    """

    def get_source(self, chunk_id: int) -> dict[str, object] | None:
        """معرف المقطع ← {id, title, text, subject, lesson} أو None."""
        ...


class FileRepositoryPort(Protocol):
    """عقد ملفات data: سرد آمن داخل الجذر + قراءة نصية محدودة."""

    def list(self, subdir: str = "") -> list[str]:
        """مجلد فرعي نسبي ← أسماء مرتبة أو [] عند الغياب."""
        ...

    def read(self, name: str, max_chars: int = 6000) -> str | None:
        """اسم ملف نسبي ← نصه أو None (مفقود/كبير/غير نصي)."""
        ...
