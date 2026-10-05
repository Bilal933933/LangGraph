"""اختبارات مجلد موجهات الاستيضاح (وهمي بلا Gemini)."""

from app.graph.edges.plan import (
    PlanExtractTarget,
    route_after_plan_extract,
)
from app.graph.edges.plan.profile import route_after_profile_extract
from app.graph.edges.plan.quiz import route_after_extract
from app.graph.edges.plan.shared import has_missing


def test_shared_detects_missing() -> None:
    assert has_missing({"messages": [], "missing_fields": ["topic"]}) is True  # type: ignore[typeddict-item]
    assert has_missing({"messages": [], "missing_fields": []}) is False  # type: ignore[typeddict-item]


def test_lesson_router() -> None:
    missing = {"messages": [], "missing_fields": ["topic"]}  # type: ignore[typeddict-item]
    complete = {"messages": [], "missing_fields": []}  # type: ignore[typeddict-item]
    assert route_after_plan_extract(missing) == "plan_ask"
    assert route_after_plan_extract(complete) == "plan_retrieve"
    assert PlanExtractTarget is not None


def test_quiz_router() -> None:
    missing = {"messages": [], "missing_fields": ["topic"]}  # type: ignore[typeddict-item]
    complete = {"messages": [], "missing_fields": []}  # type: ignore[typeddict-item]
    assert route_after_extract(missing) == "ask_clarification"
    assert route_after_extract(complete) == "confirm_ready"


def test_profile_router() -> None:
    named = {"messages": [], "pending_profile_name": "أحمد"}  # type: ignore[typeddict-item]
    empty = {"messages": [], "pending_profile_name": None}  # type: ignore[typeddict-item]
    assert route_after_profile_extract(named) == "save_profile"
    assert route_after_profile_extract(empty) == "ask_profile_name"


def test_legacy_imports_still_work() -> None:
    from app.graph.edges import extract as legacy_extract
    from app.graph.edges import profile as legacy_profile

    complete = {"messages": [], "missing_fields": []}  # type: ignore[typeddict-item]
    assert legacy_extract.route_after_extract(complete) == "confirm_ready"
    assert legacy_profile.route_after_profile_extract({"messages": []}) == "ask_profile_name"  # type: ignore[typeddict-item]
