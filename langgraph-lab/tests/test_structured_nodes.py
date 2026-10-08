"""اختبارات الربط المهيكل: retry واحدة ثم خطأ صريح، وحفظ المسودات."""

from typing import Any

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.core.errors import AppError, ErrorCode
from app.domain.models import QuizRequest, WorksheetRequest
from app.domain.outputs.quiz import QuizOutput
from app.domain.outputs.worksheet import WorksheetOutput
from app.graph.nodes.quiz_agent import make_quiz_agent_node
from app.graph.nodes.structured_retry import parse_with_retry
from app.graph.nodes.worksheet import make_worksheet_write_node


def _quiz() -> QuizOutput:
    return QuizOutput.model_validate(
        {
            "topic": "QT",
            "grade_level": "QG",
            "questions": [
                {
                    "type": "mcq",
                    "stem": "QS",
                    "options": ["A", "B", "C", "D"],
                    "answer_index": 1,
                    "explanation": "QE",
                    "points": 100,
                }
            ],
        }
    )


def _sheet() -> WorksheetOutput:
    return WorksheetOutput.model_validate(
        {
            "kind": "worksheet",
            "topic": "WT",
            "grade_level": "WG",
            "items": [{"instruction": "WI", "expected_answer": "WA"}],
        }
    )


class ScriptedStructured:
    def __init__(self, outputs: list[Any]) -> None:
        self._outputs = outputs
        self.calls = 0
        self.last_count = 0

    def parse(self, messages: list[BaseMessage], schema: type[Any]) -> Any:
        _ = schema
        self.calls += 1
        self.last_count = len(messages)
        out = self._outputs[min(self.calls - 1, len(self._outputs) - 1)]
        if isinstance(out, Exception):
            raise out
        return out


class FixedModel:
    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        _ = (messages, callbacks)
        return AIMessage(content="TEXT-REPLY")


def _fail() -> AppError:
    return AppError(ErrorCode.INVALID_MODEL_OUTPUT, "bad shape")


def test_retry_succeeds_first_try() -> None:
    fake = ScriptedStructured([_quiz()])
    out = parse_with_retry(fake, [HumanMessage(content="hi")], QuizOutput)
    assert isinstance(out, QuizOutput) and fake.calls == 1


def test_retry_once_then_succeeds() -> None:
    fake = ScriptedStructured([_fail(), _quiz()])
    first_len = 1
    out = parse_with_retry(fake, [HumanMessage(content="hi")], QuizOutput)
    assert isinstance(out, QuizOutput)
    assert fake.calls == 2
    assert fake.last_count == first_len + 1


def test_double_failure_raises() -> None:
    fake = ScriptedStructured([_fail(), _fail()])
    with pytest.raises(AppError):
        parse_with_retry(fake, [HumanMessage(content="hi")], QuizOutput)
    assert fake.calls == 2


def test_quiz_agent_structured_stores_draft_and_hides() -> None:
    node = make_quiz_agent_node(FixedModel(), ScriptedStructured([_quiz()]))  # type: ignore[arg-type]
    state = {
        "messages": [HumanMessage(content="quiz please")],
        "quiz_request": QuizRequest(topic="QT", grade_level="QG", num_questions=1),
    }
    result = node(state)  # type: ignore[arg-type]
    assert isinstance(result["quiz_draft"], QuizOutput)
    texts = [str(m.content) for m in result["messages"]]  # type: ignore[union-attr]
    assert any("QS" in t for t in texts)
    assert all("QE" not in t for t in texts)


def test_quiz_agent_legacy_without_structured() -> None:
    node = make_quiz_agent_node(FixedModel())  # type: ignore[arg-type]
    state = {"messages": [HumanMessage(content="quiz please")]}
    result = node(state)  # type: ignore[arg-type]
    assert "quiz_draft" not in result
    texts = [str(m.content) for m in result["messages"]]  # type: ignore[union-attr]
    assert texts == ["TEXT-REPLY"]


def test_worksheet_write_structured() -> None:
    node = make_worksheet_write_node(FixedModel(), structured=ScriptedStructured([_sheet()]))  # type: ignore[arg-type]
    state = {
        "messages": [HumanMessage(content="sheet please")],
        "worksheet_request": WorksheetRequest(topic="WT", grade_level="WG"),
    }
    result = node(state)  # type: ignore[arg-type]
    assert isinstance(result["worksheet_draft"], WorksheetOutput)
    texts = [str(m.content) for m in result["messages"]]  # type: ignore[union-attr]
    assert any("WI" in t for t in texts)
    assert all("WA" not in t for t in texts)

