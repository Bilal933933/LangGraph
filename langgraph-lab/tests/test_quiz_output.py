"""اختبارات المخرج المهيكل للاختبار والحجب من الخادم."""

import pytest
from pydantic import ValidationError

from app.domain.outputs.quiz import QuizOutput
from app.evals.quiz_checks import evaluate_quiz_output
from app.rendering.quiz_paper import render_quiz_output


def _quiz_dict() -> dict:
    return {
        "topic": "TOPIC-X",
        "grade_level": "GRADE-Y",
        "questions": [
            {
                "type": "mcq",
                "stem": "STEM-1",
                "options": ["A1", "B1", "C1", "D1"],
                "answer_index": 2,
                "explanation": "EXP-1",
                "points": 50,
            },
            {
                "type": "true_false",
                "stem": "STEM-2",
                "options": ["True-Opt", "False-Opt"],
                "answer_index": 0,
                "explanation": "EXP-2",
                "points": 50,
            },
        ],
    }


def test_valid_output_parses() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    assert quiz.schema_version == "v1"
    assert len(quiz.questions) == 2


def test_mcq_requires_four_options() -> None:
    bad = _quiz_dict()
    bad["questions"][0]["options"] = ["A1", "B1", "C1"]
    with pytest.raises(ValidationError):
        QuizOutput.model_validate(bad)


def test_answer_index_out_of_range_rejected() -> None:
    bad = _quiz_dict()
    bad["questions"][0]["answer_index"] = 9
    with pytest.raises(ValidationError):
        QuizOutput.model_validate(bad)


def test_duplicate_options_rejected() -> None:
    bad = _quiz_dict()
    bad["questions"][0]["options"] = ["A1", "A1", "C1", "D1"]
    with pytest.raises(ValidationError):
        QuizOutput.model_validate(bad)


def test_student_copy_hides_answers() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    text = render_quiz_output(quiz, show_answers=False)
    assert "STEM-1" in text
    assert "C1" in text
    assert "EXP-1" not in text
    assert "EXP-2" not in text
    assert "TOPIC-X" in text


def test_teacher_copy_shows_answers() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    text = render_quiz_output(quiz, show_answers=True)
    assert "EXP-1" in text
    assert "C1" in text


def test_evaluate_output() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    result = evaluate_quiz_output(quiz, 2)
    assert result["valid"] is True
    assert result["count_ok"] is True
    assert result["schema_version"] == "v1"
    assert result["total_points"] == 100
    assert result["total_mismatch"] is False


def test_total_mismatch_flagged() -> None:
    raw = _quiz_dict()
    raw["questions"][0]["points"] = 30
    raw["questions"][1]["points"] = 30
    quiz = QuizOutput.model_validate(raw)
    result = evaluate_quiz_output(quiz, 2)
    assert result["total_points"] == 60
    assert result["total_mismatch"] is True
    assert "المجموع: 60" in render_quiz_output(quiz)


def test_missing_points_distributed_equally() -> None:
    raw = _quiz_dict()
    raw["questions"][0]["points"] = 0
    raw["questions"][1]["points"] = 0
    raw["questions"].append(
        {
            "type": "short_answer",
            "stem": "STEM-3",
            "options": [],
            "answer_index": None,
            "explanation": "",
            "points": 0,
        }
    )
    quiz = QuizOutput.model_validate(raw)
    text = render_quiz_output(quiz)
    assert "المجموع: 100" in text
    assert "(34 درجات)" in text
    assert "(33 درجات)" in text


def test_option_letters_are_alif_ba_jeem_dal() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    text = render_quiz_output(quiz)
    for letter in ("أ)", "ب)", "ج)", "د)"):
        assert letter in text
    assert "ة)" not in text


def test_header_shows_computed_total() -> None:
    quiz = QuizOutput.model_validate(_quiz_dict())
    assert "المجموع: 100" in render_quiz_output(quiz)

