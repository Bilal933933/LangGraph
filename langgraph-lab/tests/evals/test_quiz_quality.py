"""جودة الاختبار حتميًا: عينات مُنسقة ← فحوصات هيكلية (إشارات انحدار)."""

import json
from pathlib import Path

from app.evals.quiz_checks import evaluate_quiz_text


def _samples() -> list[dict[str, object]]:
    raw = json.loads((Path(__file__).parent / "quiz_samples.json").read_text(encoding="utf-8"))
    assert isinstance(raw, list) and raw
    return [dict(s) for s in raw]


def test_quiz_samples_meet_expectations() -> None:
    for sample in _samples():
        assert isinstance(sample["text"], str)
        assert isinstance(sample["topic"], str)
        assert isinstance(sample["grade"], str)
        assert isinstance(sample["num_questions"], int)
        result = evaluate_quiz_text(
            str(sample["text"]),
            str(sample["topic"]),
            str(sample["grade"]),
            int(sample["num_questions"]),
        )
        expected = dict(sample["expected"])  # type: ignore[arg-type]
        assert result["topic_mentioned"] is expected["topic"], sample["id"]
        assert result["grade_mentioned"] is expected["grade"], sample["id"]
        meets = bool(result["question_count"] >= int(sample["num_questions"]))
        assert meets is expected["meets_count"], sample["id"]
        assert result["has_answer_key"] is expected["answer_key"], sample["id"]
