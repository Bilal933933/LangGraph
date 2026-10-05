"""اختبارات حقل الاستيضاح المهيكل (وهمي بلا Gemini)."""

from app.domain.models import ClarificationOut
from app.graph.nodes.plan import build_plan_clarification


def test_missing_returns_clarification() -> None:
    result = build_plan_clarification(
        {"messages": [], "missing_fields": ["grade_level", "minutes"]}  # type: ignore[arg-type]
    )
    assert isinstance(result, ClarificationOut)
    assert result.kind == "plan"
    assert result.missing == ["grade_level", "minutes"]
    assert result.suggestions["minutes"] == ["30", "45", "60"]
    assert result.profile_empty is True


def test_profile_grades_become_suggestions() -> None:
    result = build_plan_clarification(
        {  # type: ignore[arg-type]
            "messages": [],
            "missing_fields": ["grade_level"],
            "profile_snapshot": {"name": "أحمد", "subject": "نحو", "grades": ["الثالث", "الرابع"]},
        }
    )
    assert result is not None
    assert result.suggestions["grade_level"] == ["الثالث", "الرابع"]
    assert result.profile_empty is False


def test_complete_returns_none() -> None:
    assert build_plan_clarification({"messages": [], "missing_fields": []}) is None  # type: ignore[arg-type]
