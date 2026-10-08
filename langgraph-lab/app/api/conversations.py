"""مسارات محادثات المسجل (HTTP فقط، المنطق في conversation_service)."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.schemas import (
    ConversationCreate,
    ConversationDetailOut,
    ConversationOut,
    MessageOut,
    SendMessageIn,
    SendMessageOut,
)
from app.auth.deps import get_current_user, get_db
from app.auth.models import User
from app.core.limits import limit_user_chat
from app.db.models.conversation import Conversation
from app.services import conversation_service as service

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def get_conversation_graph() -> Any:
    """رسم المحادثات: مفوض للمصنع الوحيد (يُستبدل في الاختبارات)."""
    from app.runtime.factory import get_shared_graph

    return await get_shared_graph()


def _to_out(conv: Conversation) -> ConversationOut:
    ordered = sorted(conv.messages, key=lambda m: (m.id or 0))
    last = ordered[-1].content if ordered else ""
    return ConversationOut(
        id=conv.id,
        title=conv.title,
        message_count=len(ordered),
        last_message=last[:120],
        updated_at=conv.updated_at,
    )


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def post_conversation(
    payload: ConversationCreate,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ConversationOut:
    """ينشئ محادثة فارغة للمالك."""
    return _to_out(service.create_conversation(session, user, payload.title))


@router.get("", response_model=list[ConversationOut])
def get_conversations(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[ConversationOut]:
    """يسرد محادثاتي مع معاينة الأخيرة."""
    return [_to_out(conv) for conv in service.list_conversations(session, user)]


@router.get("/{conversation_id}", response_model=ConversationDetailOut)
def get_conversation(
    conversation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> ConversationDetailOut:
    """سجل محادثة واحدة (الملكية تُفحص أولًا)."""
    conv = service.get_conversation(session, user, conversation_id)
    return ConversationDetailOut(
        id=conv.id,
        title=conv.title,
        messages=[
            MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
            for m in conv.messages
        ],
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(
    conversation_id: int,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    """يحذف محادثتي ورسائلها."""
    service.delete_conversation(session, user, conversation_id)


@router.post("/{conversation_id}/messages", response_model=SendMessageOut)
async def post_message(
    conversation_id: int,
    payload: SendMessageIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    graph: Annotated[Any, Depends(get_conversation_graph)],
    _: Annotated[None, Depends(limit_user_chat)],
) -> SendMessageOut:
    """يرسل رسالة ضمن محادثتي: ملكية ← حفظ ← رسم ← حفظ الرد مع مصادره."""
    from app.api.schemas import ClarificationOut, SourceOut

    detail = await service.send_message_detail(
        session, graph, user, conversation_id, payload.message
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
    return SendMessageOut(
        reply=reply,
        sources=[SourceOut(**s) if isinstance(s, dict) else SourceOut() for s in sources],
        clarification=clarification,
    )
