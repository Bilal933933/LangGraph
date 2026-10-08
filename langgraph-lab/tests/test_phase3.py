"""اختبارات المرحلة 3: حلقة الوكيل والأدوات (وهمي بلا Gemini)."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.domain.models import IntentResult, QuizRequest
from app.domain.outputs.quiz import QuizOutput
from app.domain.ports import ChatModelPort
from app.graph.builder import build_graph
from app.graph.edges import route_after_agent
from app.graph.tools import make_fetch_lesson_tool
from app.services.chat_service import ChatService

T = TypeVar("T", bound=BaseModel)

_FULL_QUIZ = QuizRequest(topic="الكسور", grade_level="الصف الرابع", num_questions=5)


class DictRepo:
    """مستودع دروس وهمي في الذاكرة."""

    def __init__(self, content: str | None = "محتوى الكسور التجريبي") -> None:
        self.calls: list[str] = []
        self._content = content

    def get(self, topic: str) -> str | None:
        self.calls.append(topic)
        return self._content


class FakeStructuredQuiz:
    """منفذ مهيكل وهمي: نية توليد وطلب مكتمل دائما."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = messages
        if schema is IntentResult:
            return cast("T", IntentResult(intent="generate_quiz"))
        if schema is QuizRequest:
            return cast("T", _FULL_QUIZ)
        if schema is QuizOutput:
            return cast(
                "T",
                QuizOutput.model_validate(
                    {
                        "topic": "الكسور",
                        "grade_level": "الصف الرابع",
                        "questions": [
                            {
                                "type": "mcq",
                                "stem": "اختبار الكسور: ما بسط الكسر 1/2؟",
                                "options": ["1", "2", "3", "4"],
                                "answer_index": 0,
                                "explanation": "البسط هو العدد العلوي",
                                "points": 100,
                            }
                        ],
                    }
                ),
            )
        raise AssertionError(f"unexpected schema {schema}")


class FakeAgentModel:
    """نموذج وكيلي وهمي: يستدعي الأداة أولا ثم يرد نهائيا."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "fetch_lesson",
                        "args": {"topic": "الكسور"},
                        "id": "call_1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(content="اختبار الكسور: 1) ما البسط؟")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = (messages, callbacks)
        yield "اختبار الكسور: 1) ما البسط؟"

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


def _service(repo: DictRepo) -> tuple[ChatService, FakeAgentModel, DictRepo]:
    agent = FakeAgentModel()
    tools = [make_fetch_lesson_tool(repo)]
    graph = build_graph(agent, FakeStructuredQuiz(), tools)
    return ChatService(graph), agent, repo


def test_agent_loop_uses_tool_then_answers() -> None:
    service, agent, repo = _service(DictRepo())
    reply = service.handle_message("اختبار من 5 أسئلة عن الكسور للصف الرابع")
    assert "اختبار الكسور" in reply
    assert agent.calls == 2
    assert repo.calls == ["الكسور"]


def test_missing_lesson_still_finishes() -> None:
    service, agent, repo = _service(DictRepo(content=None))
    reply = service.handle_message("اختبار من 5 أسئلة عن الكسور للصف الرابع")
    assert "اختبار الكسور" in reply
    assert agent.calls == 2
    assert repo.calls == ["الكسور"]


def test_route_after_agent() -> None:
    calling = AIMessage(
        content="", tool_calls=[{"name": "t", "args": {}, "id": "1", "type": "tool_call"}]
    )
    assert route_after_agent({"messages": [calling]}) == "tools"
    assert route_after_agent({"messages": [AIMessage(content="done")]}) == "end"
