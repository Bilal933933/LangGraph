"""ميزانية الرموز: جمع الاستخدام + سقف يومي يحجب قبل الرسم."""

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, BaseMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import conversations as conv_routes
from app.auth import security
from app.auth.deps import get_db
from app.auth.models import User  # noqa: F401 - تسجيل الجداول في Base
from app.core.config import get_settings
from app.core.usage import UsageCollector, get_today_usage, record_usage, today_utc
from app.db.engine import dispose_engine
from app.db.models import Base
from app.db.models.teacher import Teacher  # noqa: F401 - تسجيل الجدول في Base
from app.main import create_app
from app.services import conversation_service as service


def _llm_result(prompt: int, completion: int) -> Any:
    message = AIMessage(
        content="x",
        response_metadata={
            "usage_metadata": {
                "prompt_token_count": prompt,
                "candidates_token_count": completion,
            }
        },
    )
    gen = SimpleNamespace(message=message)
    return SimpleNamespace(generations=[[gen]], llm_output={})


def test_collector_sums_gemini_usage() -> None:
    collector = UsageCollector()
    collector.on_llm_end(_llm_result(100, 40))
    collector.on_llm_end(_llm_result(10, 5))
    assert (collector.input_tokens, collector.output_tokens) == (110, 45)


def test_collector_falls_back_to_llm_output() -> None:
    message = AIMessage(content="x")
    gen = SimpleNamespace(message=message)
    usage = {"prompt_tokens": 7, "completion_tokens": 3}
    result = SimpleNamespace(generations=[[gen]], llm_output={"token_usage": usage})
    collector = UsageCollector()
    collector.on_llm_end(result)
    assert (collector.input_tokens, collector.output_tokens) == (7, 3)


def test_record_and_read_daily_usage() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sess = Session(engine)
    try:
        record_usage(sess, "user:9", 100, 50)
        record_usage(sess, "user:9", 25, 25)
        sess.commit()
        assert get_today_usage(sess, "user:9") == (125, 75)
        assert get_today_usage(sess, "user:10") == (0, 0)
        assert get_today_usage(sess, "user:9", day=today_utc().replace(year=2000)) == (0, 0)
    finally:
        sess.close()
        dispose_engine(engine)


def test_answer_node_forwards_config_callbacks() -> None:
    from app.graph.nodes.answer import make_answer_node

    seen: dict[str, Any] = {}

    class RecordingModel:
        def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
            _ = messages
            return AIMessage(content="hi")

        async def astream(self, messages: list[BaseMessage], callbacks: Any = None):  # type: ignore[no-untyped-def]
            _ = messages
            seen["callbacks"] = callbacks
            yield "hi"

        def bind_tools(self, tools: Any) -> Any:
            _ = tools
            return self

    import asyncio

    async def _run() -> None:
        node = make_answer_node(RecordingModel())  # type: ignore[arg-type]
        await node({"messages": []}, {"callbacks": ["cb"]})  # type: ignore[arg-type]

    asyncio.run(_run())
    assert seen["callbacks"] == ["cb"]


def _client(sess: Session) -> TestClient:
    from langgraph.checkpoint.memory import InMemorySaver

    from app.graph.builder import build_graph
    from tests.test_conversations import FakeModel
    from tests.test_phase1 import FakeStructuredGeneral

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


def test_budget_cap_blocks_before_graph(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "daily_token_cap", 100)
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    try:
        user = User(email="b@example.com", password_hash=security.hash_password("secret123"))
        sess.add(user)
        sess.commit()
        conv = service.create_conversation(sess, user, "t")
        sess.commit()
        record_usage(sess, f"user:{user.id}", 10_000_000, 0)
        sess.commit()
        token = security.issue_access_token(
            user.id, get_settings().jwt_secret.get_secret_value(), 15
        )
        client = _client(sess)
        res = client.post(
            f"/conversations/{conv.id}/messages",
            json={"message": "مرحبا"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 429, res.text
        assert res.json()["error"]["code"] == "TOKEN_BUDGET_EXCEEDED"
    finally:
        sess.close()
        dispose_engine(engine)
