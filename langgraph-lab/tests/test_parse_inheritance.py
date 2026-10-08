"""اختبارات انقطاع الالتصاق: النية السابقة لا تورث بعد اكتمال الطلب."""

from langchain_core.messages import HumanMessage

from app.domain.models import CanonicalRequest
from app.graph.nodes.parse import make_parse_request_node


class ScriptedStructured:
    """منفذ مهيكل وهمي يعيد طلبات مجهزة بالترتيب."""

    def __init__(self, outputs: list[CanonicalRequest]) -> None:
        self._outputs = outputs

    def parse(self, messages: object, schema: object) -> CanonicalRequest:
        _ = (messages, schema)
        return self._outputs[0]


def _run(
    prev: CanonicalRequest | None,
    fresh: CanonicalRequest,
    missing_fields: list[str] | None = None,
) -> CanonicalRequest:
    node = make_parse_request_node(ScriptedStructured([fresh]))
    state: dict[str, object] = {"messages": [HumanMessage(content="x")]}
    if prev is not None:
        state["canonical_request"] = prev
    if missing_fields is not None:
        state["missing_fields"] = missing_fields
    result = node(state)  # type: ignore[arg-type]
    merged = result["canonical_request"]
    assert isinstance(merged, CanonicalRequest)
    return merged


def test_greeting_does_not_stick() -> None:
    prev = CanonicalRequest(intent="greeting", missing=[])
    fresh = CanonicalRequest(intent="general_question")
    assert _run(prev, fresh).intent == "general_question"


def test_completed_plan_does_not_regenerate_on_side_question() -> None:
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", grade_level="الخامس", missing=[]
    )
    fresh = CanonicalRequest(intent="general_question")
    out = _run(prev, fresh)
    assert out.intent == "general_question"
    assert out.topic is None


def test_update_profile_does_not_stick() -> None:
    prev = CanonicalRequest(intent="update_profile", missing=[])
    fresh = CanonicalRequest(intent="general_question")
    assert _run(prev, fresh).intent == "general_question"


def test_unsupported_does_not_stick() -> None:
    prev = CanonicalRequest(intent="unsupported", missing=[])
    fresh = CanonicalRequest(intent="general_question")
    assert _run(prev, fresh).intent == "general_question"


def test_incomplete_plan_resumes_on_ambiguous() -> None:
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", grade_level="الخامس",
        missing=["minutes"],
    )
    fresh = CanonicalRequest(intent="general_question")
    out = _run(prev, fresh)
    assert out.intent == "plan_lesson"
    assert out.topic == "الكسور"


def test_incomplete_plan_merges_explicit_refinement() -> None:
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", grade_level="الخامس",
        missing=["minutes"],
    )
    fresh = CanonicalRequest(intent="plan_lesson", topic="الكسور")
    out = _run(prev, fresh)
    assert out.intent == "plan_lesson"
    assert out.topic == "الكسور"
    assert out.grade_level == "الخامس"


def test_incomplete_plan_switches_on_explicit_new_intent() -> None:
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", missing=["minutes"]
    )
    fresh = CanonicalRequest(intent="generate_quiz", topic="الكسور")
    assert _run(prev, fresh).intent == "generate_quiz"


def test_minutes_only_in_missing_fields_resumes() -> None:
    """السيناريو الحقيقي: canonical.missing فارغ وminutes في missing_fields."""
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", grade_level="الخامس", missing=[]
    )
    # المحلل الحقيقي قد يصنف "45 دقيقة" غامضة (general_question).
    fresh = CanonicalRequest(intent="general_question")
    out = _run(prev, fresh, missing_fields=["minutes"])
    assert out.intent == "plan_lesson"
    assert out.topic == "الكسور"


def test_quiz_count_only_in_missing_fields_resumes() -> None:
    prev = CanonicalRequest(
        intent="generate_quiz", topic="الكسور", grade_level="الرابع", missing=[]
    )
    fresh = CanonicalRequest(intent="general_question")
    out = _run(prev, fresh, missing_fields=["num_questions"])
    assert out.intent == "generate_quiz"


def test_completed_explicit_new_plan_no_topic_inheritance() -> None:
    """مكتمل + plan صريح جديد: لا وراثة للموضوع أو الصف (يسأل من جديد)."""
    prev = CanonicalRequest(
        intent="plan_lesson", topic="الكسور", grade_level="الخامس", missing=[]
    )
    fresh = CanonicalRequest(intent="plan_lesson", topic="الجمع")
    out = _run(prev, fresh, missing_fields=[])
    assert out.intent == "plan_lesson"
    assert out.topic == "الجمع"
    assert out.grade_level is None


def test_router_resumes_via_missing_fields_union() -> None:
    """الموجه يستخدم الاتحاد أيضا: canonical فارغ + missing_fields."""
    from app.graph.edges.request import route_by_request

    state = {
        "messages": [],
        "canonical_request": CanonicalRequest(
            intent="general_question", topic="الكسور", missing=[]
        ),
        "missing_fields": ["minutes"],
        "lesson_request": {"topic": "الكسور"},
    }
    assert route_by_request(state) == "plan_extract"  # type: ignore[arg-type]
