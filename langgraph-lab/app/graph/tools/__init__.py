"""تصدير أدوات الوكيل (التوافق: `from app.graph.tools import ...`)."""

from app.graph.tools.files import make_list_files_tool as make_list_files_tool
from app.graph.tools.files import make_read_file_tool as make_read_file_tool
from app.graph.tools.knowledge import make_search_knowledge_tool as make_search_knowledge_tool
from app.graph.tools.lesson import make_fetch_lesson_tool as make_fetch_lesson_tool
from app.graph.tools.source import make_fetch_source_tool as make_fetch_source_tool

__all__ = [
    "make_fetch_lesson_tool",
    "make_fetch_source_tool",
    "make_list_files_tool",
    "make_read_file_tool",
    "make_search_knowledge_tool",
]
