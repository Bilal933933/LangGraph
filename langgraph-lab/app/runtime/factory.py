"""مصنع Runtime الوحيد: بناء Graph مرة واحدة وحقن Tools من مكان واحد.

القاعدة: API لا يبني Graph ولا يقرر Tools. الكل يمر من هنا.
السلوك الحالي محفوظ: لا LessonRepository إنتاجي بعد، لذا الأدوات []
عبر `build_default_tools()` كنقطة حقن لاحقة (المرحلة 6).
"""

from typing import Any

from langchain_core.tools import BaseTool

from app.core.config import Settings, get_settings
from app.graph.builder import build_graph, create_model, create_structured
from app.graph.checkpoints import (
    async_postgres_checkpointer_cm,
    create_checkpointer,
)
from app.repositories.pg_knowledge import PgKnowledgeRepository
from app.repositories.sql_teacher import SqlTeacherDirectory, SqlTeacherProfile
from app.services.chat_service import ChatService

#: سياق AsyncPostgresSaver الحي (اتصال واحد لعمر العملية). يُغلق عند الإيقاف.
#: الدخول لسياق غير متزامن يتطلب حلقة حدث، لذلك التهيئة والإغلاق
#: غير متزامنين ويُستدعيان من lifespan أو أول طلب (يعمل داخل الحدث).
_ASYNC_STACK: Any | None = None
_POSTGRES_INSTANCE: list[object] = []
_SHARED_GRAPH: list[object] = []
_CHAT_SERVICE: list[object] = []


async def resolve_checkpointer() -> object:
    """بلا DATABASE_URL ← ذاكرة مؤقتة. معه ← AsyncPostgresSaver دائم.

    غير متزامنة لأن دخول سياق الحافظ غير المتزامن يحتاج حلقة حدث.
    """
    from contextlib import AsyncExitStack

    global _ASYNC_STACK
    database_url = get_settings().database_url.get_secret_value().strip()
    if not database_url:
        return create_checkpointer()
    if _POSTGRES_INSTANCE:
        return _POSTGRES_INSTANCE[0]
    stack = AsyncExitStack()
    instance = await stack.enter_async_context(async_postgres_checkpointer_cm(database_url))
    _ASYNC_STACK = stack
    _POSTGRES_INSTANCE.append(instance)
    return instance


async def close_checkpointer() -> None:
    """يغلق اتصال AsyncPostgresSaver عند إيقاف التطبيق."""
    global _ASYNC_STACK
    if _ASYNC_STACK is not None:
        await _ASYNC_STACK.aclose()
        _ASYNC_STACK = None
    _POSTGRES_INSTANCE.clear()
    _SHARED_GRAPH.clear()
    _CHAT_SERVICE.clear()


def build_default_tools(lesson_repo: Any | None = None) -> list[BaseTool]:
    """نقطة حقن الأدوات الوحيدة. بلا مستودع ← [] (تطوير/اختبارات)."""
    if lesson_repo is None:
        return []
    from app.graph.tools import make_fetch_lesson_tool

    return [make_fetch_lesson_tool(lesson_repo)]


def build_knowledge_tools(knowledge: Any | None) -> list[BaseTool]:
    """أدوات الوكيل المعرفية: بحث ← قراءة. بلا معرفة ← [] (السلوك محفوظ)."""
    if knowledge is None:
        return []
    from app.graph.tools import make_fetch_source_tool, make_search_knowledge_tool

    return [make_search_knowledge_tool(knowledge), make_fetch_source_tool(knowledge)]


def build_local_file_tools(repo: Any | None = None) -> list[BaseTool]:
    """أدوات ملفات data/ المحلية: سرد ← قراءة. تعمل دائمًا بلا DB."""
    from app.graph.tools import make_list_files_tool, make_read_file_tool

    if repo is None:
        from app.repositories.local_files import LocalFilesRepository

        repo = LocalFilesRepository()
    return [make_list_files_tool(repo), make_read_file_tool(repo)]


class KnowledgeLessonAdapter:
    """محول LessonRepository فوق المعرفة: أول مقطع ← نص الدرس أو None."""

    def __init__(self, knowledge: Any) -> None:
        self._knowledge = knowledge

    def get(self, topic: str) -> str | None:
        """موضوع الدرس ← نص أعلى مقطع أو None عند الفراغ/الفشل."""
        cleaned = topic.strip()[:500]
        if not cleaned:
            return None
        try:
            chunks = self._knowledge.search(cleaned, 1)
        except Exception:
            return None
        if not chunks:
            return None
        text = str(chunks[0].get("text") or "").strip()
        return text or None


def create_app_graph(settings: Settings, checkpointer: Any) -> Any:
    """يبني Graph التطبيق: model + structured + tools + مخازن من مكان واحد.

    الإنتاج (DATABASE_URL موجود): knowledge حقيقية ← أداة fetch_lesson مربوطة.
    التطوير/الاختبارات: بلا DB ← أداتا ملفات data/ فقط (list_files/read_file).
    الحلقة quiz_agent ⇄ quiz_tools محدودة بـ recursion_limit=12 في ChatService.
    """
    model = create_model(settings)
    structured = create_structured(settings)
    database_url = settings.database_url.get_secret_value().strip()
    directory = SqlTeacherDirectory(database_url) if database_url else None
    knowledge = PgKnowledgeRepository(database_url) if database_url else None
    lesson_repo = KnowledgeLessonAdapter(knowledge) if knowledge is not None else None
    tools = (
        build_default_tools(lesson_repo)
        + build_knowledge_tools(knowledge)
        + build_local_file_tools()
    )
    graph = build_graph(
        model,
        structured,
        tools,
        checkpointer=checkpointer,
        teacher_directory=directory,
        profile_writer=directory,
        profile_store=SqlTeacherProfile(database_url) if database_url else None,
        knowledge=knowledge,
    )
    return graph


async def get_shared_graph() -> Any:
    """Graph واحد مشترك لكل المسارات (يُستبدل في الاختبارات).

    غير متزامنة لأن الحافظ قد يحتاج دخول سياق غير متزامن.
    """
    if _SHARED_GRAPH:
        return _SHARED_GRAPH[0]
    settings = get_settings()
    graph = create_app_graph(settings, await resolve_checkpointer())
    _SHARED_GRAPH.append(graph)
    return graph


async def get_chat_service() -> ChatService:
    """يبني الخدمة مرة واحدة فوق Graph المشترك (توفير التكلفة)."""
    if _CHAT_SERVICE:
        service = _CHAT_SERVICE[0]
        assert isinstance(service, ChatService)
        return service
    service = ChatService(await get_shared_graph())
    _CHAT_SERVICE.append(service)
    return service
