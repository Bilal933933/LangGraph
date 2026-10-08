"""اختبارات موجه النية: استكمال + تحية لاحقة + نية غريبة."""

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.edges.intent import route_by_intent


def test_greeting_later_goes_to_answer() -> None:
    state = {
        "messages": [HumanMessage(content="مرحبا"), AIMessage(content="أهلا")],
        "intent": "greeting",
    }
    assert route_by_intent(state) == "answer"  # type: ignore[arg-type]


def test_greeting_first_goes_to_answer() -> None:
    from app.graph.edges.request import route_by_request

    state = {
        "messages": [HumanMessage(content="مرحبا")],
        "intent": "greeting",
    }
    assert route_by_intent(state) == "answer"  # type: ignore[arg-type]
    assert route_by_request(state) == "answer"  # type: ignore[arg-type]


def test_incomplete_quiz_resumes_extract() -> None:
    state = {
        "messages": [],
        "intent": "general_question",
        "missing_fields": ["topic"],
        "quiz_request": {"topic": None},
    }
    assert route_by_intent(state) == "extract"  # type: ignore[arg-type]


def test_both_requests_prefers_plan() -> None:
    state = {
        "messages": [],
        "intent": "greeting",
        "missing_fields": ["topic"],
        "lesson_request": {"topic": None},
        "quiz_request": {"topic": None},
    }
    assert route_by_intent(state) == "plan_extract"  # type: ignore[arg-type]


def test_unknown_intent_falls_back_to_answer() -> None:
    state = {"messages": [], "intent": "strange_value"}
    assert route_by_intent(state) == "answer"  # type: ignore[arg-type]
