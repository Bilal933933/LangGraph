"""اختبارات المرحلة 2: تصنيف واستخراج مولد الاختبارات (وهمي بلا Gemini)."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.domain.models import Intent, IntentResult, QuizRequest
from app.domain.ports import ChatModelPort
from app.graph.builder import build_graph
from app.graph.edges import route_after_extract, route_by_intent
from app.services.chat_service import ChatService

T = TypeVar("T", bound=BaseModel)


class FakeChat:
    """نموذج نصي وهمي."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        self.calls += 1
        return AIMessage(content=f"fake-reply-to-{len(messages)}-messages")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = callbacks
        self.calls += 1
        yield f"fake-reply-to-{len(messages)}-messages"

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


class FakeStructured:
    """منفذ مهيكل وهمي بنية وقالب قابلين للضبط."""

    def __init__(
        self, intent: Intent = "general_question", quiz: QuizRequest | None = None
    ) -> None:
        self._intent = intent
        self._quiz = quiz or QuizRequest()

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = messages
        if schema is IntentResult:
            return cast("T", IntentResult(intent=self._intent))
        if schema is QuizRequest:
            return cast("T", self._quiz)
        raise AssertionError(f"unexpected schema {schema}")


class FakeStructuredFailOnce(FakeStructured):
    """يفشل مرة ثم ينجح (يثبت إعادة المحاولة)."""

    def __init__(self) -> None:
        super().__init__(intent="greeting")
        self.attempts = 0

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        if schema is IntentResult:
            self.attempts += 1
            if self.attempts == 1:
                raise ValueError("bad output")
            return cast("T", IntentResult(intent="greeting"))
        return super().parse(messages, schema)


class FakeStructuredAlwaysFail:
    """يفشل دائما (يثبت السقوط الناعم)."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = (messages, schema)
        raise ValueError("bad output")


def _service(intent: Intent, quiz: QuizRequest | None = None) -> tuple[ChatService, FakeChat]:
    chat = FakeChat()
    return ChatService(build_graph(chat, FakeStructured(intent=intent, quiz=quiz), [])), chat


def test_greeting_skips_llm() -> None:
    service, chat = _service("greeting")
    assert "أهلاً بك" in service.handle_message("مرحبا")
    assert chat.calls == 0


def test_general_question_uses_llm() -> None:
    service, chat = _service("general_question")
    assert service.handle_message("اشرح الكسور") == "fake-reply-to-1-messages"
    assert chat.calls == 1


def test_unsupported_declines() -> None:
    service, chat = _service("unsupported")
    assert "خارج نطاق" in service.handle_message("اكتب كود اختراق")
    assert chat.calls == 0


def test_complete_quiz_confirms_then_agent_runs() -> None:
    quiz = QuizRequest(topic="الكسور", grade_level="الصف الرابع", num_questions=5)
    service, chat = _service("generate_quiz", quiz)
    reply = service.handle_message("اختبار من 5 أسئلة عن الكسور للصف الرابع")
    assert reply.startswith("fake-reply-to-")
    assert chat.calls == 1


def test_missing_fields_asks_clarification() -> None:
    quiz = QuizRequest(topic="الكسور")
    service, _ = _service("generate_quiz", quiz)
    reply = service.handle_message("اختبار عن الكسور")
    assert "لم تحدد" in reply
    assert "المستوى الدراسي" in reply


def test_classify_retries_then_succeeds() -> None:
    service = ChatService(build_graph(FakeChat(), FakeStructuredFailOnce(), []))
    assert "أهلاً بك" in service.handle_message("مرحبا")


def test_classify_falls_back_to_general() -> None:
    chat = FakeChat()
    service = ChatService(build_graph(chat, FakeStructuredAlwaysFail(), []))
    assert service.handle_message("???") == "fake-reply-to-1-messages"
    assert chat.calls == 1


def test_routes() -> None:
    assert route_by_intent({"messages": [], "intent": "greeting"}) == "greeting"
    assert route_by_intent({"messages": [], "intent": "general_question"}) == "answer"
    assert route_by_intent({"messages": [], "intent": "unsupported"}) == "decline"
    assert route_by_intent({"messages": [], "intent": "generate_quiz"}) == "extract"
    assert route_after_extract({"messages": [], "missing_fields": ["topic"]}) == "ask_clarification"
    assert route_after_extract({"messages": [], "missing_fields": []}) == "confirm_ready"
