"""اختبارات سجل المخرجات (نية ← مخطط/عارض)."""

import pytest

from app.domain.models import LessonPlan
from app.domain.outputs.quiz import QuizOutput
from app.domain.outputs.worksheet import WorksheetOutput
from app.rendering.registry import output_schema_for, render_for_intent


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


def _plan() -> LessonPlan:
    return LessonPlan(topic="PT", grade_level="PG", minutes=45)


def test_schema_lookup() -> None:
    assert output_schema_for("generate_quiz") is QuizOutput
    assert output_schema_for("generate_worksheet") is WorksheetOutput
    assert output_schema_for("plan_lesson") is LessonPlan


def test_unknown_intent_rejected() -> None:
    with pytest.raises(ValueError):
        output_schema_for("general_question")


def test_render_quiz_hides_by_default() -> None:
    text = render_for_intent("generate_quiz", _quiz())
    assert "QS" in text
    assert "QE" not in text


def test_render_quiz_teacher_copy() -> None:
    text = render_for_intent("generate_quiz", _quiz(), show_answers=True)
    assert "QE" in text


def test_render_worksheet_hides_by_default() -> None:
    text = render_for_intent("generate_worksheet", _sheet())
    assert "WI" in text
    assert "WA" not in text


def test_render_plan() -> None:
    text = render_for_intent("plan_lesson", _plan())
    assert "PT" in text


def test_mismatch_rejected() -> None:
    with pytest.raises(ValueError):
        render_for_intent("generate_quiz", _sheet())

