"""اختبارات المرحلة 2: توجيه شرطي حسب النية بدون Gemini الحقيقي."""

from langchain_core.messages import BaseMessage, HumanMessage

from app.domain.state import ChatState
from app.graph.builder import build_graph, route_by_intent
from app.graph.nodes import classify_node
from app.services.chat_service import ChatService


class FakeModel:
    """نموذج وهمي يحقق ChatModelPort."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages: list[BaseMessage]) -> str:
        self.calls += 1
        return f"fake-reply-to-{len(messages)}-messages"


def _state(text: str) -> ChatState:
    return {"messages": [HumanMessage(content=text)]}


def test_classify_greeting() -> None:
    assert classify_node(_state("مرحبا")) == {"intent": "greeting"}


def test_classify_question() -> None:
    assert classify_node(_state("كيف أبني رسما في LangGraph؟")) == {"intent": "question"}


def test_classify_chat() -> None:
    assert classify_node(_state("حدثني عن إدارة الحالة")) == {"intent": "chat"}


def test_route_maps_intents() -> None:
    assert route_by_intent({"messages": [], "intent": "greeting"}) == "greeting"
    assert route_by_intent({"messages": [], "intent": "question"}) == "question"
    assert route_by_intent({"messages": []}) == "chat"


def test_greeting_skips_llm() -> None:
    model = FakeModel()
    service = ChatService(build_graph(model))
    reply = service.handle_message("مرحبا")
    assert "أهلاً بك" in reply
    assert model.calls == 0


def test_question_uses_llm() -> None:
    model = FakeModel()
    service = ChatService(build_graph(model))
    reply = service.handle_message("كيف أبني رسما؟")
    assert reply == "fake-reply-to-1-messages"
    assert model.calls == 1


def test_regression_substrings_are_not_greetings() -> None:
    assert classify_node(_state("history of Rome")) == {"intent": "chat"}
    assert classify_node(_state("ship it")) == {"intent": "chat"}
    assert classify_node(_state("whisper")) == {"intent": "chat"}


def test_regression_question_beats_greeting_word() -> None:
    assert classify_node(_state("hi, how do I use LangGraph?")) == {"intent": "question"}
