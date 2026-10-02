"""المسارات (Routes = نقاط استقبال HTTP بدون منطق)."""

from functools import lru_cache

from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse
from app.core.config import get_settings
from app.graph.builder import build_graph, create_model
from app.services.chat_service import ChatService

router = APIRouter(tags=["chat"])


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """يبني الرسم مرة واحدة ويعيد استخدامه (توفير التكلفة)."""
    settings = get_settings()
    model = create_model(settings)
    graph = build_graph(model)
    return ChatService(graph)


@router.get("/health")
def health() -> dict[str, str]:
    """فحص الحياة."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def post_chat(payload: ChatRequest) -> ChatResponse:
    """يستقبل رسالة ← يعيد رد Gemini عبر الرسم."""
    service = get_chat_service()
    reply = service.handle_message(payload.message)
    return ChatResponse(reply=reply)
