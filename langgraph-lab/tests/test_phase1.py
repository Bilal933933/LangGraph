"""اختبارات المرحلة 1: رسم خطي من عقدتين بدون استدعاء Gemini الحقيقي."""

from fastapi.testclient import TestClient
from langchain_core.messages import BaseMessage

from app.api import routes
from app.graph.builder import build_graph
from app.main import create_app
from app.services.chat_service import ChatService


class FakeModel:
    """نموذج وهمي يحقق ChatModelPort للاختبار المعزول."""

    def invoke(self, messages: list[BaseMessage]) -> str:
        return f"fake-reply-to-{len(messages)}-messages"


def test_graph_runs_two_nodes_in_order() -> None:
    graph = build_graph(FakeModel())
    service = ChatService(graph)
    reply = service.handle_message("حدثني عن إدارة الحالة")
    assert reply == "fake-reply-to-1-messages"


def test_post_chat_uses_service() -> None:
    graph = build_graph(FakeModel())
    routes.get_chat_service.cache_clear()
    app = create_app()
    app.dependency_overrides = {}
    # حقن خدمة وهمية عبر التخزين المؤقت
    routes.get_chat_service.cache_clear()
    original = routes.get_chat_service

    def _fake() -> ChatService:
        return ChatService(graph)

    routes.get_chat_service = _fake  # type: ignore[assignment]
    try:
        client = TestClient(app, raise_server_exceptions=False)
        res = client.post("/chat", json={"message": "حدثني عن إدارة الحالة"})
        assert res.status_code == 200, res.text
        assert res.json()["reply"] == "fake-reply-to-1-messages"
    finally:
        routes.get_chat_service = original
        routes.get_chat_service.cache_clear()


def test_health() -> None:
    app = create_app()
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
