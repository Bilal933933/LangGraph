"""اختبارات المرحلة 1: المسار العام عبر الرسم الجديد بدون Gemini الحقيقي."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.api import routes
from app.domain.models import IntentResult
from app.domain.ports import ChatModelPort
from app.graph.builder import build_graph
from app.main import create_app
from app.services.chat_service import ChatService

T = TypeVar("T", bound=BaseModel)


class FakeModel:
    """نموذج وهمي يحقق ChatModelPort للاختبار المعزول."""

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        return AIMessage(content=f"fake-reply-to-{len(messages)}-messages")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = callbacks
        yield f"fake-reply-to-{len(messages)}-messages"

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


class FakeStructuredGeneral:
    """منفذ مهيكل وهمي يعيد نية general_question دائما."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = messages
        assert schema is IntentResult
        return cast("T", IntentResult(intent="general_question"))


def test_graph_runs_two_nodes_in_order() -> None:
    graph = build_graph(FakeModel(), FakeStructuredGeneral(), [])
    service = ChatService(graph)
    reply = service.handle_message("حدثني عن إدارة الحالة")
    assert reply == "fake-reply-to-1-messages"


def test_post_chat_uses_service() -> None:
    graph = build_graph(FakeModel(), FakeStructuredGeneral(), [])
    app = create_app()
    app.dependency_overrides = {}

    async def _fake() -> ChatService:
        return ChatService(graph)

    app.dependency_overrides[routes.get_chat_service] = _fake
    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.post("/chat", json={"message": "حدثني عن إدارة الحالة"})
        assert res.status_code == 200, res.text
        assert res.json()["reply"] == "fake-reply-to-1-messages"
    finally:
        app.dependency_overrides = {}


def test_health() -> None:
    app = create_app()
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
