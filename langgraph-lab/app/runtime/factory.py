"""مصنع Runtime الوحيد: بناء Graph مرة واحدة وحقن Tools من مكان واحد.

القاعدة: API لا يبني Graph ولا يقرر Tools. الكل يمر من هنا.
السلوك الحالي محفوظ: لا LessonRepository إنتاجي بعد، لذا الأدوات []
عبر `build_default_tools()` كنقطة حقن لاحقة (المرحلة 6).
"""

from functools import lru_cache
from typing import Any

from langchain_core.tools import BaseTool

from app.core.config import Settings, get_settings
from app.graph.builder import build_graph, create_model, create_structured
from app.graph.checkpoints import (
    create_checkpointer,
    postgres_checkpointer_cm,
)
from app.repositories.pg_knowledge import PgKnowledgeRepository
from app.repositories.sql_teacher import SqlTeacherDirectory, SqlTeacherProfile
from app.services.chat_service import ChatService

#: سياق PostgresSaver الحي (اتصال واحد لعمر العملية). يُغلق عند الإيقاف.
_POSTGRES_STACK: list[object] = []
_POSTGRES_INSTANCE: list[object] = []


def resolve_checkpointer() -> object:
    """بلا DATABASE_URL ← ذاكرة مؤقتة. معه ← PostgresSaver دائم."""
    from contextlib import ExitStack

    database_url = get_settings().database_url.get_secret_value().strip()
    if not database_url:
        return create_checkpointer()
    if _POSTGRES_INSTANCE:
        return _POSTGRES_INSTANCE[0]
    stack = ExitStack()
    instance = stack.enter_context(postgres_checkpointer_cm(database_url))
    _POSTGRES_STACK.append(stack)
    _POSTGRES_INSTANCE.append(instance)
    return instance


def close_checkpointer() -> None:
    """يغلق اتصال PostgresSaver عند إيقاف التطبيق."""
    while _POSTGRES_STACK:
        stack = _POSTGRES_STACK.pop()
        stack.close()  # type: ignore[attr-defined]
    _POSTGRES_INSTANCE.clear()


def build_default_tools(lesson_repo: Any | None = None) -> list[BaseTool]:
    """نقطة حقن الأدوات الوحيدة. بلا مستودع ← [] (تطوير/اختبارات)."""
    if lesson_repo is None:
        return []
    from app.graph.tools import make_fetch_lesson_tool

    return [make_fetch_lesson_tool(lesson_repo)]


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
    التطوير/الاختبارات: بلا DB ← tools=[] والسلوك محفوظ.
    الحلقة محدودة بـ recursion_limit=12 في ChatService.
    """
    model = create_model(settings)
    structured = create_structured(settings)
    database_url = settings.database_url.get_secret_value().strip()
    directory = SqlTeacherDirectory(database_url) if database_url else None
    knowledge = PgKnowledgeRepository(database_url) if database_url else None
    lesson_repo = KnowledgeLessonAdapter(knowledge) if knowledge is not None else None
    graph = build_graph(
        model,
        structured,
        build_default_tools(lesson_repo),
        checkpointer=checkpointer,
        teacher_directory=directory,
        profile_writer=directory,
        profile_store=SqlTeacherProfile(database_url) if database_url else None,
        knowledge=knowledge,
    )
    return graph


@lru_cache(maxsize=1)
def get_shared_graph() -> Any:
    """Graph واحد مشترك لكل المسارات (يُستبدل في الاختبارات)."""
    settings = get_settings()
    return create_app_graph(settings, resolve_checkpointer())


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """يبني الخدمة مرة واحدة فوق Graph المشترك (توفير التكلفة)."""
    return ChatService(get_shared_graph())
