"""اختبارات المخرج المهيكل لورقة العمل والحجب من الخادم."""

import pytest
from pydantic import ValidationError

from app.domain.outputs.worksheet import WorksheetOutput
from app.evals.worksheet_checks import evaluate_worksheet_output
from app.rendering.worksheet_paper import render_worksheet_output


def _sheet_dict() -> dict:
    return {
        "kind": "worksheet",
        "topic": "TOPIC-X",
        "grade_level": "GRADE-Y",
        "items": [
            {
                "instruction": "INST-1",
                "expected_answer": "ANS-1",
                "differentiation": "support",
                "minutes": 5,
            },
            {
                "instruction": "INST-2",
                "expected_answer": "ANS-2",
                "differentiation": "core",
                "minutes": 0,
            },
        ],
    }


def test_valid_output_parses() -> None:
    sheet = WorksheetOutput.model_validate(_sheet_dict())
    assert sheet.schema_version == "v1"
    assert len(sheet.items) == 2


def test_blank_instruction_rejected() -> None:
    bad = _sheet_dict()
    bad["items"][0]["instruction"] = "   "
    with pytest.raises(ValidationError):
        WorksheetOutput.model_validate(bad)


def test_too_many_items_rejected() -> None:
    bad = _sheet_dict()
    bad["items"] = [dict(bad["items"][0]) for _ in range(31)]
    with pytest.raises(ValidationError):
        WorksheetOutput.model_validate(bad)


def test_student_copy_hides_key() -> None:
    sheet = WorksheetOutput.model_validate(_sheet_dict())
    text = render_worksheet_output(sheet, show_answers=False)
    assert "INST-1" in text
    assert "ANS-1" not in text
    assert "ANS-2" not in text
    assert "TOPIC-X" in text


def test_teacher_copy_shows_key() -> None:
    sheet = WorksheetOutput.model_validate(_sheet_dict())
    text = render_worksheet_output(sheet, show_answers=True)
    assert "ANS-1" in text
    assert "ANS-2" in text


def test_activity_header() -> None:
    raw = _sheet_dict()
    raw["kind"] = "activity"
    raw["minutes"] = 20
    sheet = WorksheetOutput.model_validate(raw)
    text = render_worksheet_output(sheet)
    assert "TOPIC-X" in text
    assert "20" in text


def test_evaluate_output() -> None:
    sheet = WorksheetOutput.model_validate(_sheet_dict())
    result = evaluate_worksheet_output(sheet, 2)
    assert result["valid"] is True
    assert result["count_ok"] is True
    assert result["has_differentiation"] is True
    assert result["schema_version"] == "v1"

