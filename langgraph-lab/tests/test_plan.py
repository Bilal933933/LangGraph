"""اختبارات التحضير: كشف التهرب وبوابة الدمج (وهمي بلا Gemini)."""

from collections.abc import AsyncIterator
from typing import Any, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool

from app.domain.models import LessonPlan, LessonRequest
from app.domain.ports import ChatModelPort
from app.graph.content import message_text
from app.graph.nodes.plan import is_evasive, make_plan_extract_node, make_plan_merge_node

_EVASIVE = "يبدو أنك نسيت تحديد الموضوع! زودني بالموضوع وسأبدأ فوراً في انتظارك."

_GOOD = (
    "أهداف الدرس: أن يعرّف الطالب الفاعل تعريفاً صحيحاً، وأن يميز الفاعل "
    "في الجملة الفعلية تمييزاً دقيقاً، وأن يعرب الفاعل إعراباً صحيحاً "
    "في تدريبات متنوعة من الكتاب المدرسي."
)


class FixedModel:
    """نموذج إصلاح وهمي: يرد قسماً سليماً دائماً."""

    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        _ = messages
        self.calls += 1
        return AIMessage(content=_GOOD)

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = (messages, callbacks)
        self.calls += 1
        yield _GOOD

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return cast("ChatModelPort", self)


def test_is_evasive_flags_placeholders() -> None:
    assert is_evasive(_EVASIVE) is True
    assert is_evasive("x") is True
    assert is_evasive(_GOOD) is False
    assert is_evasive(_GOOD, topic="المفعول المطلق") is True
    assert is_evasive(_GOOD, topic="الفاعل") is False


def test_merge_repairs_evasive_sections_once() -> None:
    model = FixedModel()
    merge = make_plan_merge_node(model)
    state = {
        "messages": [],
        "lesson_request": LessonRequest(topic="الفاعل", grade_level="الثالث", minutes=45),
        "retrieved_sources": [],
        "plan_sections": [
            {"kind": "objectives", "title": "objectives", "body": _EVASIVE},
            {"kind": "intro", "title": "intro", "body": _GOOD},
            {"kind": "steps", "title": "steps", "body": _GOOD},
            {"kind": "activities", "title": "activities", "body": _GOOD},
            {"kind": "assessment", "title": "assessment", "body": _GOOD},
        ],
    }
    result = merge(state)  # type: ignore[arg-type]
    plan = cast("LessonPlan", result["plan_draft"])
    assert plan.topic == "الفاعل"
    assert "يعرّف الطالب الفاعل" in plan.objectives
    assert model.calls == 1


def test_merge_without_model_keeps_sections() -> None:
    merge = make_plan_merge_node(None)
    state = {
        "messages": [],
        "lesson_request": LessonRequest(topic="الفاعل", grade_level="الثالث", minutes=45),
        "retrieved_sources": [],
        "plan_sections": [
            {"kind": k, "title": k, "body": _GOOD} for k in
            ("objectives", "intro", "steps", "activities", "assessment")
        ],
    }
    result = merge(state)  # type: ignore[arg-type]
    assert cast("LessonPlan", result["plan_draft"]).minutes == 45


class _MinutesOnlyStructured:
    """منفذ مهيكل وهمي: يستخرج الدقائق من آخر رسالة بشرية فقط."""

    def parse(self, messages: list[BaseMessage], schema: type[LessonRequest]) -> LessonRequest:
        _ = schema
        last = message_text(messages[-1].content) if messages else ""
        return LessonRequest(minutes=45 if "45" in last else None)


def test_plan_extract_completes_minutes_from_short_reply() -> None:
    from langchain_core.messages import HumanMessage

    extract = make_plan_extract_node(_MinutesOnlyStructured())  # type: ignore[arg-type]
    state = {
        "messages": [HumanMessage(content="45 دقيقة")],
        "lesson_request": LessonRequest(topic="الجمع", grade_level="الثالث"),
    }
    result = extract(state)  # type: ignore[arg-type]
    req = cast("LessonRequest", result["lesson_request"])
    assert (req.topic, req.grade_level, req.minutes) == ("الجمع", "الثالث", 45)
    assert result["missing_fields"] == []
    assert result["plan_sections"] == []
