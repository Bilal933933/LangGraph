"""اختبارات محادثات المسجل (sqlite في الذاكرة، رسم وهمي بلا Gemini)."""

from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import conversations as conv_routes
from app.auth import security
from app.auth.deps import get_db
from app.auth.models import RefreshSession, User  # noqa: F401 - تسجيل الجداول في Base
from app.core.config import get_settings
from app.db.engine import dispose_engine
from app.db.models import Base
from app.db.models.teacher import Teacher  # noqa: F401 - تسجيل الجدول في Base
from app.domain.ports import ChatModelPort
from app.graph.builder import build_graph
from app.main import create_app
from tests.test_phase1 import FakeStructuredGeneral


class FakeModel:
    """نموذج وهمي يعد الرسائل ليثبت استعادة السياق."""

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        return AIMessage(content=f"fake-reply-to-{len(messages)}-messages")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = callbacks
        yield f"fake-reply-to-{len(messages)}-messages"

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self  # type: ignore[return-value]


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    try:
        yield sess
    finally:
        sess.close()
        dispose_engine(engine)


def _client(sess: Session) -> TestClient:
    app = create_app()

    def _get_db():
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    graph = build_graph(FakeModel(), FakeStructuredGeneral(), [], checkpointer=InMemorySaver())

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[conv_routes.get_conversation_graph] = lambda: graph
    return TestClient(app, raise_server_exceptions=False)


def _token_for(user_id: int) -> str:
    settings = get_settings()
    return security.issue_access_token(
        user_id, settings.jwt_secret.get_secret_value(), settings.jwt_access_minutes
    )


def _register(sess: Session, email: str) -> User:
    user = User(email=email, password_hash="x")
    sess.add(user)
    sess.commit()
    return user


def test_create_and_list_are_scoped_to_owner(session: Session) -> None:
    client = _client(session)
    alice = _register(session, "alice@example.com")
    bob = _register(session, "bob@example.com")
    headers_a = {"Authorization": f"Bearer {_token_for(alice.id)}"}
    headers_b = {"Authorization": f"Bearer {_token_for(bob.id)}"}

    res = client.post("/conversations", json={"title": "اختبار"}, headers=headers_a)
    assert res.status_code == 201, res.text

    assert len(client.get("/conversations", headers=headers_a).json()) == 1
    assert client.get("/conversations", headers=headers_b).json() == []


def test_cannot_read_or_delete_other_conversation(session: Session) -> None:
    client = _client(session)
    alice = _register(session, "alice@example.com")
    bob = _register(session, "bob@example.com")
    headers_a = {"Authorization": f"Bearer {_token_for(alice.id)}"}
    headers_b = {"Authorization": f"Bearer {_token_for(bob.id)}"}

    conv_id = client.post("/conversations", json={}, headers=headers_a).json()["id"]

    assert client.get(f"/conversations/{conv_id}", headers=headers_b).status_code == 404
    assert client.delete(f"/conversations/{conv_id}", headers=headers_b).status_code == 404
    assert client.get(f"/conversations/{conv_id}", headers=headers_a).status_code == 200


def test_send_message_saves_history_and_resumes(session: Session) -> None:
    client = _client(session)
    alice = _register(session, "alice@example.com")
    headers = {"Authorization": f"Bearer {_token_for(alice.id)}"}

    conv_id = client.post("/conversations", json={}, headers=headers).json()["id"]

    first = client.post(
        f"/conversations/{conv_id}/messages", json={"message": "اهلا"}, headers=headers
    )
    assert first.status_code == 200, first.text
    assert first.json()["reply"] == "fake-reply-to-2-messages"

    second = client.post(
        f"/conversations/{conv_id}/messages", json={"message": "كمل"}, headers=headers
    )
    assert second.status_code == 200, second.text
    assert second.json()["reply"] == "fake-reply-to-4-messages"

    detail = client.get(f"/conversations/{conv_id}", headers=headers).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]


def test_delete_removes_conversation_and_messages(session: Session) -> None:
    client = _client(session)
    alice = _register(session, "alice@example.com")
    headers = {"Authorization": f"Bearer {_token_for(alice.id)}"}

    conv_id = client.post("/conversations", json={}, headers=headers).json()["id"]
    client.post(f"/conversations/{conv_id}/messages", json={"message": "اهلا"}, headers=headers)

    assert client.delete(f"/conversations/{conv_id}", headers=headers).status_code == 204
    assert client.get(f"/conversations/{conv_id}", headers=headers).status_code == 404


def test_requires_auth(session: Session) -> None:
    client = _client(session)
    assert client.get("/conversations").status_code in (401, 403)
    assert client.post("/conversations", json={}).status_code in (401, 403)
