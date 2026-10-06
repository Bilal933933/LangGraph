"""أدوات الملفات المحلية (سرد/قراءة data/ داخل حلقة الوكيل)."""

from langchain_core.tools import BaseTool, tool

from app.core.trace import get_logger
from app.domain.ports import FileRepositoryPort

logger = get_logger(__name__)


def make_list_files_tool(repo: FileRepositoryPort) -> BaseTool:
    """مصنع السرد: مجلد فرعي ← أسماء مرتبة أو رسالة غياب."""

    @tool
    def list_files(subdir: str = "") -> str:
        """يسرد ملفات ومجلدات data/ (فارغ=الجذر، وإلا مسار نسبي آمن)."""
        cleaned = (subdir or "").strip()[:500]
        try:
            names = repo.list(cleaned)
        except Exception as exc:
            logger.warning("files_list_failed subdir=%r error=%r", cleaned, exc)
            return "تعذر سرد المجلد الآن."
        if not names:
            return f"لا يوجد محتوى في: {cleaned or 'data/'}."
        return "المحتوى:\n" + "\n".join(f"- {n}" for n in list(names)[:100])

    return list_files


def make_read_file_tool(repo: FileRepositoryPort) -> BaseTool:
    """مصنع القراءة: اسم ملف نسبي ← نصه أو رسالة إرشاد."""

    @tool
    def read_file(name: str) -> str:
        """يقرأ ملفًا نصيًا من data/ بمساره النسبي (حد 6000 حرف)."""
        cleaned = (name or "").strip()[:500]
        if not cleaned:
            return "اكتب اسم ملف نسبي داخل data/ أولًا (مثال: textbook/.../part-01.md)."
        try:
            text = repo.read(cleaned)
        except Exception as exc:
            logger.warning("files_read_failed name=%r error=%r", cleaned, exc)
            return "تعذر قراءة الملف الآن."
        if not text:
            return f"لا يوجد ملف نصي صالح: {cleaned}."
        return str(text)[:6000]

    return read_file
