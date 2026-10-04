"""المسارات (Routes = نقاط استقبال HTTP بدون منطق)."""

from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import get_settings
from app.graph.builder import build_graph, create_model, create_structured
from app.graph.checkpoints import (
    create_checkpointer,
    postgres_checkpointer_cm,
)
from app.graph.tools import make_fetch_lesson_tool
from app.repositories.json_lesson import JsonLessonRepository
from app.repositories.sql_teacher import SqlTeacherDirectory, SqlTeacherProfile
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])

LESSONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "lessons.json"

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


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """يبني الرسم مرة واحدة ويعيد استخدامه (توفير التكلفة)."""
    settings = get_settings()
    model = create_model(settings)
    structured = create_structured(settings)
    tools = [make_fetch_lesson_tool(JsonLessonRepository(LESSONS_FILE))]
    database_url = settings.database_url.get_secret_value().strip()
    directory = SqlTeacherDirectory(database_url) if database_url else None
    graph = build_graph(
        model,
        structured,
        tools,
        checkpointer=resolve_checkpointer(),
        teacher_directory=directory,
        profile_writer=directory,
        profile_store=SqlTeacherProfile(database_url) if database_url else None,
    )
    return ChatService(graph)


@router.get("/health")
def health() -> dict[str, str]:
    """فحص الحياة."""
    return {"status": "ok"}


@router.get("/health/db")
def health_db() -> dict[str, str]:
    """فحص اتصال DB فقط: SELECT 1. فارغ الرابط = غير مُعد."""
    from app.db.engine import check_connection, get_engine

    database_url = get_settings().database_url.get_secret_value().strip()
    if not database_url:
        return {"db": "not_configured"}
    engine = get_engine(database_url)
    try:
        check_connection(engine)
    finally:
        engine.dispose()
    return {"db": "ok"}


@router.post("/chat", response_model=ChatResponse)
def post_chat(payload: ChatRequest) -> ChatResponse:
    """يستقبل رسالة ← يعيد رد Gemini عبر الرسم."""
    service = get_chat_service()
    reply = service.handle_message(payload.message, thread_id=payload.thread_id)
    return ChatResponse(reply=reply)
