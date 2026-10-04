"""مسارات محادثات المسجل (HTTP فقط، المنطق في conversation_service)."""

from functools import lru_cache
from pathlib import Path
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
from app.db.models.conversation import Conversation
from app.services import conversation_service as service

router = APIRouter(prefix="/conversations", tags=["conversations"])

LESSONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "lessons.json"


@lru_cache(maxsize=1)
def get_conversation_graph() -> Any:
    """رسم المحادثات: يُبنى مرة واحدة (يُستبدل في الاختبارات)."""
    from app.api.routes import resolve_checkpointer
    from app.core.config import get_settings
    from app.graph.builder import build_graph, create_model, create_structured
    from app.graph.tools import make_fetch_lesson_tool
    from app.repositories.json_lesson import JsonLessonRepository
    from app.repositories.sql_teacher import SqlTeacherDirectory, SqlTeacherProfile

    settings = get_settings()
    model = create_model(settings)
    structured = create_structured(settings)
    tools = [make_fetch_lesson_tool(JsonLessonRepository(LESSONS_FILE))]
    database_url = settings.database_url.get_secret_value().strip()
    directory = SqlTeacherDirectory(database_url) if database_url else None
    return build_graph(
        model,
        structured,
        tools,
        checkpointer=resolve_checkpointer(),
        teacher_directory=directory,
        profile_writer=directory,
        profile_store=SqlTeacherProfile(database_url) if database_url else None,
    )


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
def post_message(
    conversation_id: int,
    payload: SendMessageIn,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
    graph: Annotated[Any, Depends(get_conversation_graph)],
) -> SendMessageOut:
    """يرسل رسالة ضمن محادثتي: ملكية ← حفظ ← رسم ← حفظ الرد."""
    reply = service.send_message(session, graph, user, conversation_id, payload.message)
    return SendMessageOut(reply=reply)
