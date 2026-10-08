"""مشغل الذهبي: نظافة البيانات + عقد العقدة + التوجيه + حي (اختياري).

الحي يتطلب RUN_LIVE_EVALS=1 ومفتاحًا حقيقيًا، ويُتخطى في CI.
"""

import json
import os
from pathlib import Path
from typing import TypeVar, cast

import pytest
from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from app.domain.models import DEFAULT_INTENT, INTENT_VALUES, CanonicalRequest, Intent
from app.domain.state import ChatState
from app.graph.edges.request import RequestTarget, route_by_request
from app.graph.nodes.parse import make_parse_request_node

T = TypeVar("T", bound=BaseModel)

_GOLDEN = json.loads(
    (Path(__file__).parent / "quiz_classification_golden.json").read_text(encoding="utf-8")
)


def _rows() -> list[dict[str, str]]:
    assert isinstance(_GOLDEN, list) and _GOLDEN
    return [dict(r) for r in _GOLDEN]


class ScriptedStructured:
    """منفذ مهيكل مُسَيَّر: نص الدخل ← النية المسجلة (بلا شبكة)."""

    def __init__(self, mapping: dict[str, str]) -> None:
        self._mapping = mapping

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        last = ""
        for message in reversed(messages):
            if isinstance(message, HumanMessage) and str(message.content).strip():
                last = str(message.content).strip()
                break
        return cast("T", CanonicalRequest(intent=cast("Intent", self._mapping[last.split(" الطلب السابق:")[0]])))


class AlwaysFailStructured:
    """يفشل دائمًا (يثبت السقوط الناعم للعقدة)."""

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = (messages, schema)
        raise ValueError("bad output")


def test_golden_intents_are_known() -> None:
    for row in _rows():
        assert row["expected_intent"] in INTENT_VALUES, row


def test_parse_node_returns_port_intent_verbatim() -> None:
    mapping = {row["input"]: row["expected_intent"] for row in _rows()}
    node = make_parse_request_node(ScriptedStructured(mapping))
    for row in _rows():
        state: ChatState = {"messages": [HumanMessage(content=row["input"])]}
        result = node(state)
        assert result["intent"] == row["expected_intent"]


def test_parse_node_falls_back_on_failure() -> None:
    node = make_parse_request_node(AlwaysFailStructured())
    state: ChatState = {"messages": [HumanMessage(content="اختبار")]}
    assert node(state)["intent"] == DEFAULT_INTENT


_EXPECTED_ROUTES: dict[str, RequestTarget] = {
    "greeting": "answer",
    "general_question": "answer",
    "generate_quiz": "extract",
    "generate_worksheet": "worksheet_extract",
    "plan_lesson": "plan_extract",
    "unsupported": "decline",
    "update_profile": "extract_profile",
}


def test_golden_intents_route_to_valid_nodes() -> None:
    for row in _rows():
        state: ChatState = {"messages": [], "intent": cast("Intent", row["expected_intent"])}
        assert route_by_request(state) == _EXPECTED_ROUTES[row["expected_intent"]]


@pytest.mark.live
def test_classification_accuracy_live() -> None:
    """دقة التصنيف بالنموذج الحقيقي (≥8/10). يتخطى بلا RUN_LIVE_EVALS=1."""
    if os.getenv("RUN_LIVE_EVALS") != "1":
        pytest.skip("live evals opt-in only")
    from app.core.config import get_settings
    from app.graph.adapters import GeminiStructuredModel

    settings = get_settings()
    key = settings.google_api_key.get_secret_value().strip()
    if not key:
        pytest.skip("no GOOGLE_API_KEY")
    node = make_parse_request_node(GeminiStructuredModel(key, settings.gemini_model))
    hits = 0
    for row in _rows():
        state: ChatState = {"messages": [HumanMessage(content=row["input"])]}
        if node(state).get("intent") == row["expected_intent"]:
            hits += 1
    assert hits >= 8, f"accuracy {hits}/{len(_rows())}"
