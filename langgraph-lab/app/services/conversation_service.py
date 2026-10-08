"""Use Case المحادثات المملوكة: ملكية أولًا ثم الرسم أو السجل."""

from collections.abc import AsyncIterator
from typing import Any, cast

from langchain_core.messages import BaseMessage, HumanMessage
from sqlalchemy.orm import Session

from app.auth.models import User
from app.core.errors import AppError, ErrorCode
from app.core.usage import UsageCollector, record_usage, subject_for_user
from app.db.models.conversation import Conversation
from app.db.models.message import Message
from app.db.models.teacher import Teacher
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.plan import build_plan_clarification
from app.services.chat_service import ChatService

#: طول عنوان المحادثة التلقائي من أول رسالة.
TITLE_LEN = 60


def get_or_create_teacher(session: Session, user: User) -> Teacher:
    """المستخدم ← ملف المعلم، ينشأ في أول استخدام."""
    teacher = session.query(Teacher).filter(Teacher.user_id == user.id).first()
    if teacher is not None:
        return teacher
    teacher = Teacher(user_id=user.id, name="", email=user.email)
    session.add(teacher)
    session.flush()
    return teacher


def _owned_conversation(session: Session, user: User, conversation_id: int) -> Conversation:
    """يجلب محادثة المالك فقط، غيرها ← 404 بلا تسريب وجود."""
    teacher = get_or_create_teacher(session, user)
    conv = (
        session.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.teacher_id == teacher.id)
        .first()
    )
    if conv is None:
        raise AppError(ErrorCode.NOT_FOUND, "المحادثة غير موجودة.", status=404)
    return conv


def create_conversation(session: Session, user: User, title: str = "") -> Conversation:
    """ينشئ محادثة فارغة للمالك."""
    teacher = get_or_create_teacher(session, user)
    conv = Conversation(teacher_id=teacher.id, title=title.strip()[:TITLE_LEN])
    session.add(conv)
    session.flush()
    return conv


def list_conversations(session: Session, user: User) -> list[Conversation]:
    """يسرد محادثات المالك فقط، الأحدث أولًا."""
    teacher = get_or_create_teacher(session, user)
    return (
        session.query(Conversation)
        .filter(Conversation.teacher_id == teacher.id)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .all()
    )


def get_conversation(session: Session, user: User, conversation_id: int) -> Conversation:
    """يفحص الملكية ثم يعيد المحادثة برسائلها مرتبة."""
    conv = _owned_conversation(session, user, conversation_id)
    conv.messages.sort(key=lambda m: (m.created_at is None, m.created_at, m.id))
    return conv


def delete_conversation(session: Session, user: User, conversation_id: int) -> None:
    """يحذف محادثة المالك ورسائلها (تتالٍ)."""
    session.delete(_owned_conversation(session, user, conversation_id))
    session.flush()


def send_message(session: Session, graph: Any, user: User, conversation_id: int, text: str) -> str:
    """ملكية ← حفظ user ← invoke عبر thread المالك ← حفظ assistant ← تحديث العنوان.

    غلاف متزامن للتوافق الخلفي (بلا حلقة حدث).
    """
    import asyncio

    reply = asyncio.run(send_message_detail(session, graph, user, conversation_id, text))[
        "reply"
    ]
    assert isinstance(reply, str)
    return reply


async def send_message_detail(
    session: Session, graph: Any, user: User, conversation_id: int, text: str
) -> dict[str, object]:
    """مثل send_message مع {reply, sources, clarification} للديلوج عند النواقص."""
    cleaned = text.strip()
    conv = _owned_conversation(session, user, conversation_id)
    session.add(Message(conversation_id=conv.id, role="user", content=cleaned))
    session.flush()

    thread = ChatService.thread_id_for_conversation(user.id, conv.id)
    payload: dict[str, Any] = {"messages": [HumanMessage(content=cleaned)]}
    payload["teacher_id"] = conv.teacher_id
    collector = UsageCollector()
    result: dict[str, Any] = await graph.ainvoke(
        payload,
        {
            "configurable": {"thread_id": thread},
            "recursion_limit": ChatService.MAX_STEPS,
            "callbacks": [collector],
        },
    )
    reply = message_text(result["messages"][-1].content)
    sources = result.get("retrieved_sources", [])
    if not isinstance(sources, list):
        sources = []
    clarification = build_plan_clarification(cast("ChatState", result))
    record_usage(
        session, subject_for_user(user.id), collector.input_tokens, collector.output_tokens
    )

    session.add(Message(conversation_id=conv.id, role="assistant", content=reply))
    if not conv.title:
        conv.title = cleaned[:TITLE_LEN]
    session.flush()
    return {
        "reply": reply,
        "sources": sources,
        "clarification": clarification.model_dump() if clarification is not None else None,
    }


async def stream_message_detail(
    session: Session, graph: Any, user: User, conversation_id: int, text: str
) -> AsyncIterator[dict[str, object]]:
    """يبث stage/token ثم done مع حفظ user أولًا وassistant عند الاكتمال."""
    from app.graph.streaming import stream_run

    cleaned = text.strip()
    conv = _owned_conversation(session, user, conversation_id)
    session.add(Message(conversation_id=conv.id, role="user", content=cleaned))
    session.flush()

    thread = ChatService.thread_id_for_conversation(user.id, conv.id)
    payload: dict[str, Any] = {"messages": [HumanMessage(content=cleaned)]}
    payload["teacher_id"] = conv.teacher_id
    collector = UsageCollector()
    config: dict[str, Any] = {
        "configurable": {"thread_id": thread},
        "recursion_limit": ChatService.MAX_STEPS,
        "callbacks": [collector],
    }
    async for event in stream_run(graph, payload, config):
        if event.get("type") != "done":
            yield event
            continue
        state = event.get("state")
        assert isinstance(state, dict)
        messages = state["messages"]
        assert isinstance(messages, list)
        last = messages[-1]
        assert isinstance(last, BaseMessage)
        reply = message_text(last.content)
        sources = state.get("retrieved_sources", [])
        if not isinstance(sources, list):
            sources = []
        clarification = build_plan_clarification(cast("ChatState", state))
        record_usage(
            session,
            subject_for_user(user.id),
            collector.input_tokens,
            collector.output_tokens,
        )
        session.add(Message(conversation_id=conv.id, role="assistant", content=reply))
        if not conv.title:
            conv.title = cleaned[:TITLE_LEN]
        session.flush()
        yield {
            "type": "done",
            "reply": reply,
            "sources": sources,
            "clarification": (
                clarification.model_dump() if clarification is not None else None
            ),
        }


async def teacher_copy_detail(
    session: Session, graph: Any, user: User, conversation_id: int, kind: str
) -> dict[str, object]:
    """ملكية ← قراءة مسودة الرسم ← نسخة المعلم (عرض فقط، بلا توليد ولا حفظ)."""
    from app.rendering.registry import render_teacher_copy

    conv = _owned_conversation(session, user, conversation_id)
    thread = ChatService.thread_id_for_conversation(user.id, conv.id)
    snapshot = await graph.aget_state({"configurable": {"thread_id": thread}})
    values = snapshot.values
    assert isinstance(values, dict)
    cleaned = kind.strip().lower()
    return {"kind": cleaned, "text": render_teacher_copy(values, cleaned)}
