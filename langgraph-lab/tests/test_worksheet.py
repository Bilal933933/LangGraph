"""اختبارات ورقة العمل والنشاط (وهمي بلا Gemini)."""

from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.domain.models import LessonPlan, WorksheetRequest
from app.evals.worksheet_checks import (
    count_numbered_items,
    evaluate_worksheet_text,
    has_answer_key,
    has_differentiation,
)
from app.graph.edges.request import route_by_request
from app.graph.edges.plan.worksheet import route_after_worksheet_extract
from app.graph.nodes.worksheet import (
    make_worksheet_ask_node,
    make_worksheet_extract_node,
    make_worksheet_retrieve_node,
    make_worksheet_write_node,
)
from app.graph.nodes.worksheet_bridge import (
    build_worksheet_shape_prompt,
    worksheet_request_from_plan,
)
from app.graph.prompts.responses.worksheet_paper import render_worksheet_paper

_BODY = "1) تمرين عن الكسور\n2) تمرين عن الكسور\n\nمفتاح الإجابة للمعلم: 1-أ 2-ب\nدعم للمتعثرين وإثراء للمتقدمين"


class ScriptedStructured:
    """منفذ مهيكل مُسَيَّر: يعيد الطلب الجاهز (بلا شبكة)."""

    def __init__(self, request: WorksheetRequest) -> None:
        self._request = request

    def parse(self, messages: list[BaseMessage], schema: type[Any]) -> Any:
        _ = (messages, schema)
        return self._request


class FailingStructured:
    """يفشل دائمًا (يثبت السقوط الناعم للاستخراج)."""

    def parse(self, messages: list[BaseMessage], schema: type[Any]) -> Any:
        _ = (messages, schema)
        raise ValueError("bad output")


class FixedModel:
    """نموذج وهمي: يرد نص تمارين ثابتًا ويسجل callbacks."""

    def __init__(self) -> None:
        self.seen_callbacks: Any = "unset"

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        _ = messages
        self.seen_callbacks = callbacks
        return AIMessage(content=_BODY)


class FixedKnowledge:
    """بحث وهمي: يعيد مقطعًا واحدًا."""

    def search(self, query: str, limit: int) -> list[dict[str, object]]:
        _ = (query, limit)
        return [{"title": "الكسور", "subject": "رياضيات", "lesson": "1", "text": "نص الكتاب"}]


def _state(**fields: object) -> Any:
    base: dict[str, object] = {"messages": [HumanMessage(content="ورقة عمل عن الكسور")]}
    base.update(fields)
    return base


def test_extract_complete_request() -> None:
    node = make_worksheet_extract_node(
        ScriptedStructured(
            WorksheetRequest(
                kind="worksheet", topic="الكسور", grade_level="الرابع", num_items=6
            )
        )
    )
    result = node(_state())  # type: ignore[arg-type]
    req = cast("WorksheetRequest", result["worksheet_request"])
    assert (req.topic, req.grade_level, req.num_items, req.kind) == (
        "الكسور",
        "الرابع",
        6,
        "worksheet",
    )
    assert result["missing_fields"] == []


def test_extract_reports_missing_fields() -> None:
    node = make_worksheet_extract_node(ScriptedStructured(WorksheetRequest()))
    result = node(_state())  # type: ignore[arg-type]
    assert result["missing_fields"] == ["topic", "grade_level"]
    req = cast("WorksheetRequest", result["worksheet_request"])
    assert req.kind == "worksheet"


def test_extract_merges_previous_and_plan() -> None:
    node = make_worksheet_extract_node(ScriptedStructured(WorksheetRequest(topic="الكسور")))
    prev = WorksheetRequest(topic=None, grade_level="الرابع", num_items=4)
    result = node(_state(worksheet_request=prev))  # type: ignore[arg-type]
    req = cast("WorksheetRequest", result["worksheet_request"])
    assert (req.topic, req.grade_level, req.num_items) == ("الكسور", "الرابع", 4)

    plan_node = make_worksheet_extract_node(ScriptedStructured(WorksheetRequest()))
    plan = LessonPlan(topic="الفاعل", grade_level="الثالث", minutes=45)
    filled = plan_node(_state(plan_draft=plan))  # type: ignore[arg-type]
    assert filled["missing_fields"] == []
    assert cast("WorksheetRequest", filled["worksheet_request"]).topic == "الفاعل"


def test_extract_falls_back_on_failure() -> None:
    node = make_worksheet_extract_node(FailingStructured())
    result = node(_state())  # type: ignore[arg-type]
    assert result["missing_fields"] == ["topic", "grade_level"]


def test_ask_node_lists_missing_labels() -> None:
    node = make_worksheet_ask_node()
    result = node({"messages": [], "missing_fields": ["topic"]})  # type: ignore[typeddict-item]
    text = cast("list[BaseMessage]", result["messages"])[0].content
    assert isinstance(text, str) and "موضوع الدرس" in text


def test_router_after_extract() -> None:
    assert route_after_worksheet_extract({"missing_fields": ["topic"]}) == "worksheet_ask"  # type: ignore[typeddict-item]
    assert route_after_worksheet_extract({"missing_fields": []}) == "worksheet_retrieve"  # type: ignore[typeddict-item]


def test_retrieve_stores_sources() -> None:
    node = make_worksheet_retrieve_node(FixedKnowledge())
    req = WorksheetRequest(kind="worksheet", topic="الكسور", grade_level="الرابع")
    result = node(_state(worksheet_request=req))  # type: ignore[arg-type]
    sources = cast("list[dict[str, object]]", result["retrieved_sources"])
    assert sources and sources[0]["title"] == "الكسور"


def test_write_renders_paper_and_forwards_callbacks() -> None:
    model = FixedModel()
    node = make_worksheet_write_node(model)
    req = WorksheetRequest(
        kind="worksheet", topic="الكسور", grade_level="الرابع", num_items=2
    )
    result = node(_state(worksheet_request=req), {"callbacks": ["cb"]})  # type: ignore[arg-type]
    text = cast("list[AIMessage]", result["messages"])[0].content
    assert isinstance(text, str) and "ورقة عمل: الكسور" in text
    assert model.seen_callbacks == ["cb"]


def test_bridge_and_render_activity() -> None:
    plan = LessonPlan(topic="الفاعل", grade_level="الثالث", minutes=45)
    req = worksheet_request_from_plan(plan)
    assert (req.topic, req.grade_level, req.kind) == ("الفاعل", "الثالث", "worksheet")
    shape = build_worksheet_shape_prompt(req)
    assert "ورقة عمل" in shape and "الفاعل" in shape
    paper = render_worksheet_paper(
        WorksheetRequest(kind="activity", topic="الكسور", grade_level="الرابع"), "خطوات"
    )
    assert "نشاط صفي" in paper


def test_checks_evaluate_text() -> None:
    assert count_numbered_items(_BODY) == 2
    assert has_answer_key(_BODY) is True
    assert has_differentiation(_BODY) is True
    report = evaluate_worksheet_text(_BODY, "الكسور", "الرابع", 2)
    assert report["item_count"] == 2 and report["topic_mentioned"] is True


def test_intent_routes_worksheet() -> None:
    assert route_by_request({"messages": [], "intent": "generate_worksheet"}) == "worksheet_extract"  # type: ignore[arg-type]
    resumed = route_by_request(  # type: ignore[arg-type]
        {
            "messages": [],
            "intent": "greeting",
            "missing_fields": ["topic"],
            "worksheet_request": {"topic": None},
        }
    )
    assert resumed == "worksheet_extract"
    both = route_by_request(  # type: ignore[arg-type]
        {
            "messages": [],
            "intent": "greeting",
            "missing_fields": ["topic"],
            "quiz_request": {"topic": None},
            "worksheet_request": {"topic": None},
        }
    )
    assert both == "extract"
