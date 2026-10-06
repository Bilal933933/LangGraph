"""اختبار نقطة البث HTTP: إطار SSE سليم من stage حتى done."""

import json
from collections.abc import AsyncIterator
from typing import Any

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api import conversations as conv_routes
from app.auth import security
from app.auth.deps import get_db
from app.auth.models import User  # noqa: F401 - تسجيل الجداول في Base
from app.core.config import get_settings
from app.db.engine import dispose_engine
from app.db.models import Base
from app.db.models.teacher import Teacher  # noqa: F401 - تسجيل الجدول في Base
from app.main import create_app
from app.services import conversation_service as service


class FakeStreamGraph:
    """يبث مرحلة واحدة ثم حالة نهائية مكتملة."""

    async def astream(
        self,
        payload: object,
        config: object = None,
        *,
        stream_mode: object = None,
    ) -> AsyncIterator[tuple[str, Any]]:
        _ = (payload, config, stream_mode)
        yield ("updates", {"answer": {"messages": []}})
        yield (
            "values",
            {
                "messages": [HumanMessage(content="hi"), AIMessage(content="رد متدفق")],
                "retrieved_sources": [],
            },
        )


def _client(sess: Session) -> TestClient:
    app = create_app()

    def _get_db():
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[conv_routes.get_conversation_graph] = lambda: FakeStreamGraph()
    return TestClient(app, raise_server_exceptions=False)


def test_conversation_stream_sse_framing() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    try:
        user = User(email="s@example.com", password_hash=security.hash_password("secret123"))
        sess.add(user)
        sess.commit()
        conv = service.create_conversation(sess, user, "t")
        sess.commit()
        token = security.issue_access_token(
            user.id, get_settings().jwt_secret.get_secret_value(), 15
        )
        client = _client(sess)
        with client.stream(
            "POST",
            f"/conversations/{conv.id}/messages/stream",
            json={"message": "مرحبا"},
            headers={"Authorization": f"Bearer {token}"},
        ) as res:
            assert res.status_code == 200, res.text
            assert res.headers["content-type"].startswith("text/event-stream")
            events: list[tuple[str, dict[str, Any]]] = []
            kind = ""
            for line in res.iter_lines():
                if line.startswith("event: "):
                    kind = line[len("event: ") :]
                elif line.startswith("data: "):
                    events.append((kind, json.loads(line[len("data: ") :])))
        kinds = [k for k, _ in events]
        assert kinds[0] == "stage" and kinds[-1] == "done"
        assert events[-1][1]["reply"] == "رد متدفق"
    finally:
        sess.close()
        dispose_engine(engine)
