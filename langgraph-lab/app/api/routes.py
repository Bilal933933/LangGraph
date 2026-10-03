"""المسارات (Routes = نقاط استقبال HTTP بدون منطق)."""

from functools import lru_cache

from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import get_settings
from app.graph.builder import build_graph, create_model, create_structured
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """يبني الرسم مرة واحدة ويعيد استخدامه (توفير التكلفة)."""
    settings = get_settings()
    model = create_model(settings)
    structured = create_structured(settings)
    graph = build_graph(model, structured)
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
    reply = service.handle_message(payload.message)
    return ChatResponse(reply=reply)
