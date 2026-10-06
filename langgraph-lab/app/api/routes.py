"""المسارات (Routes = نقاط استقبال HTTP بدون منطق)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.schemas import ChatRequest, ChatResponse
from app.auth.deps import get_db
from app.core.config import get_settings
from app.core.limits import client_ip, limit_guest_chat
from app.core.usage import subject_for_ip
from app.runtime.factory import close_checkpointer as close_checkpointer
from app.runtime.factory import get_chat_service as get_chat_service
from app.runtime.factory import resolve_checkpointer as resolve_checkpointer

router = APIRouter(tags=["chat"])


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
def post_chat(
    payload: ChatRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_guest_chat)],
) -> ChatResponse:
    """يستقبل رسالة ← يعيد رد Gemini عبر الرسم مع مصادره واستيضاح الديلوج."""
    from app.api.schemas import ClarificationOut, SourceOut

    service = get_chat_service()
    detail = service.handle_message_detail(
        payload.message,
        thread_id=payload.thread_id,
        session=session,
        usage_subject=subject_for_ip(client_ip(request)),
    )
    reply = detail["reply"]
    assert isinstance(reply, str)
    sources = detail["sources"]
    assert isinstance(sources, list)
    raw_clarification = detail.get("clarification")
    clarification = (
        ClarificationOut(**raw_clarification)
        if isinstance(raw_clarification, dict)
        else None
    )
    return ChatResponse(
        reply=reply,
        sources=[SourceOut(**s) if isinstance(s, dict) else SourceOut() for s in sources],
        clarification=clarification,
    )
