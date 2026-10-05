"""أداة جلب الدرس (مصنع واحد لكل ملف)."""

from langchain_core.tools import BaseTool, tool

from app.domain.ports import LessonRepository


def make_fetch_lesson_tool(repo: LessonRepository) -> BaseTool:
    """مصنع أداة جلب الدرس: تغلق على المستودع المحقون."""

    @tool
    def fetch_lesson(topic: str) -> str:
        """يجلب محتوى درس بموضوعه لاستخدامه في توليد الاختبار."""
        content = repo.get(topic)
        if content:
            return content
        return f"لا يوجد محتوى لموضوع: {topic}. ولد الاختبار من معرفتك العامة."

    return fetch_lesson
