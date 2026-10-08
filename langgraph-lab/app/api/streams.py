"""نقاط البث SSE (إطار فقط، المنطق في الخدمات)."""

from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api.conversations import get_conversation_graph
from app.api.schemas import ChatRequest, SendMessageIn
from app.auth.deps import get_current_user, get_db
from app.auth.models import User
from app.core.limits import client_ip, limit_guest_chat, limit_user_chat
from app.core.usage import subject_for_ip
from app.graph.streaming import StreamEvent, encode_sse
from app.runtime.factory import get_chat_service
from app.services import conversation_service as service

router = APIRouter(tags=["streams"])


async def _sse(events: AsyncIterator[StreamEvent]) -> StreamingResponse:
    """مولد أحداث ← استجابة SSE (يغلق عند done/error)."""

    async def gen() -> AsyncIterator[str]:
        async for event in events:
            yield encode_sse(event)

    return StreamingResponse(gen(), media_type="text/event-stream")


@router.post("/chat/stream")
async def post_chat_stream(
    payload: ChatRequest,
    request: Request,
    session: Annotated[Session, Depends(get_db)],
    _: Annotated[None, Depends(limit_guest_chat)],
    chat: Annotated[Any, Depends(get_chat_service)],
) -> StreamingResponse:
    """بث الضيوف: مراحل ← رموز ← done بالرد والمصادر."""
    return await _sse(
        chat.stream_message_detail(
            payload.message,
            chat.guest_thread_id(client_ip(request), payload.thread_id),
            session=session,
            usage_subject=subject_for_ip(client_ip(request)),
        )
    )


@router.post("/conversations/{conversation_id}/messages/stream")
async def post_message_stream(
    conversation_id: int,
    payload: SendMessageIn,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    graph: Annotated[Any, Depends(get_conversation_graph)],
    _: Annotated[None, Depends(limit_user_chat)],
) -> StreamingResponse:
    """بث المسجلين: حفظ user أولًا ثم مراحل ← رموز ← done مع حفظ الرد."""
    return await _sse(
        service.stream_message_detail(session, graph, user, conversation_id, payload.message)
    )
