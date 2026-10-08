"""مشغل ذهبي الاستخراج: سلامة البيانات دائما + دقة حية (اختيارية).

الحي يتطلب RUN_LIVE_EVALS=1 ومفتاحا حقيقيا، ويتخطى في CI.
"""

import json
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from langchain_core.messages import HumanMessage

from app.domain.models import LessonRequest, ProfileInfo, QuizRequest, WorksheetRequest
from app.graph.nodes.extract import make_extract_node
from app.graph.nodes.plan import make_plan_extract_node
from app.graph.nodes.profile import make_extract_profile_info_node
from app.graph.nodes.worksheet import make_worksheet_extract_node

_WS = re.compile(r"\s+")


def _rows(name: str) -> list[dict[str, Any]]:
    raw = json.loads((Path(__file__).parent / name).read_text(encoding="utf-8"))
    assert isinstance(raw, list) and raw
    return [dict(r) for r in raw]


def _norm(value: object) -> str:
    return _WS.sub(" ", str(value)).strip()


def _match(actual: object, expected: object) -> bool:
    if expected is None:
        return actual is None or actual == "" or actual == []
    if expected == []:
        return actual is None or actual == []
    if isinstance(expected, (int, float)):
        return actual == expected
    if isinstance(expected, list):
        if not isinstance(actual, list) or len(actual) != len(expected):
            return False
        return all(any(_match(a, e) for a in actual) for e in expected)
    a, e = _norm(actual or ""), _norm(expected)
    return bool(a) and bool(e) and (e in a or a in e)


_SUITES: list[tuple[str, Any, Callable[[Any], Any], str]] = [
    ("quiz_extract_golden.json", QuizRequest, make_extract_node, "quiz_request"),
    (
        "worksheet_extract_golden.json",
        WorksheetRequest,
        make_worksheet_extract_node,
        "worksheet_request",
    ),
    ("plan_extract_golden.json", LessonRequest, make_plan_extract_node, "lesson_request"),
    ("profile_extract_golden.json", ProfileInfo, make_extract_profile_info_node, "pending_profile"),
]


def test_golden_rows_are_valid() -> None:
    for name, schema, _, _ in _SUITES:
        rows = _rows(name)
        inputs = [str(r["input"]) for r in rows]
        assert all(inputs) and len(set(inputs)) == len(inputs), name
        for row in rows:
            assert isinstance(row["expected"], dict) and row["expected"], row
            schema(**dict(row["expected"]))


def _actual_fields(result: dict[str, object], key: str, expected: dict[str, Any]) -> dict[str, Any]:
    raw = result.get(key)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return {k: raw.get(k) for k in expected}
    return {k: getattr(raw, k, None) for k in expected}


@pytest.mark.live
def test_extract_accuracy_live() -> None:
    """دقة المستخرجات بالنموذج الحقيقي (80% مجمعة). تتخطى بلا RUN_LIVE_EVALS=1."""
    if os.getenv("RUN_LIVE_EVALS") != "1":
        pytest.skip("live evals opt-in only")
    from app.core.config import get_settings
    from app.graph.adapters import GeminiStructuredModel

    settings = get_settings()
    key = settings.google_api_key.get_secret_value().strip()
    if not key:
        pytest.skip("no GOOGLE_API_KEY")
    structured = GeminiStructuredModel(key, settings.gemini_model)
    hits = total = 0
    report: list[str] = []
    for name, _, factory, result_key in _SUITES:
        node = factory(structured)
        file_hits = 0
        rows = _rows(name)
        for row in rows:
            total += 1
            expected = dict(row["expected"])
            try:
                result = node({"messages": [HumanMessage(content=str(row["input"]))]})
                assert isinstance(result, dict)
                actual = _actual_fields(result, result_key, expected)
                ok = all(_match(actual.get(k), v) for k, v in expected.items())
            except Exception:
                ok = False
            if ok:
                hits += 1
                file_hits += 1
        report.append(f"{name}: {file_hits}/{len(rows)}")
    assert hits / total >= 0.8, f"accuracy {hits}/{total} (" + ", ".join(report) + ")"

