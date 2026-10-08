"""تسلسل سؤال الاسم: سؤال ← رد بكلمة واحدة ← حفظ."""

from langchain_core.messages import HumanMessage

from app.domain.models import CanonicalRequest, ProfileName
from app.graph.edges.plan.profile import route_after_profile_extract
from app.graph.nodes.parse import make_parse_request_node
from app.graph.nodes.profile import (
    ask_profile_name_node,
    make_extract_profile_node,
    make_save_profile_node,
)


class ScriptedCanonical:
    def __init__(self, outputs: list[CanonicalRequest]) -> None:
        self._outputs = outputs

    def parse(self, messages: object, schema: object) -> CanonicalRequest:
        _ = (messages, schema)
        return self._outputs[0]


class ScriptedProfile:
    def __init__(self, outputs: list[ProfileName]) -> None:
        self._outputs = outputs
        self.calls = 0

    def parse(self, messages: object, schema: object) -> ProfileName:
        _ = (messages, schema)
        out = self._outputs[min(self.calls, len(self._outputs) - 1)]
        self.calls += 1
        return out


class FakeWriter:
    def __init__(self) -> None:
        self.saved: list[str] = []

    def update_name(self, teacher_id: int, name: str) -> str:
        _ = teacher_id
        self.saved.append(name)
        return name


def test_ask_marks_name_missing() -> None:
    result = ask_profile_name_node({"messages": []})  # type: ignore[typeddict-item]
    assert "الاسم" in str(result["messages"][0].content)
    assert "name" in list(result.get("missing_fields", []))


def test_save_without_name_marks_missing() -> None:
    node = make_save_profile_node(FakeWriter())  # type: ignore[arg-type]
    result = node({"messages": [], "teacher_id": 7, "pending_profile_name": None})  # type: ignore[typeddict-item]
    assert "name" in list(result.get("missing_fields", []))


def test_save_success_clears_missing() -> None:
    writer = FakeWriter()
    node = make_save_profile_node(writer)  # type: ignore[arg-type]
    result = node({"messages": [], "teacher_id": 7, "pending_profile_name": "بلال"})  # type: ignore[typeddict-item]
    assert "بلال" in str(result["messages"][0].content)
    assert list(result.get("missing_fields", [])) == []
    assert writer.saved == ["بلال"]


def test_parse_resumes_name_pending_on_single_word() -> None:
    """المحلل يصنف بلال غامضة ← تستأنف update_profile لوجود name."""
    prev = CanonicalRequest(intent="update_profile", missing=[])
    fresh = CanonicalRequest(intent="general_question")
    node = make_parse_request_node(ScriptedCanonical([fresh]))
    state: dict[str, object] = {
        "messages": [HumanMessage(content="بلال")],
        "canonical_request": prev,
        "missing_fields": ["name"],
    }
    out = node(state)  # type: ignore[arg-type]
    assert out["canonical_request"].intent == "update_profile"  # type: ignore[union-attr]


def test_parse_does_not_resume_completed_profile() -> None:
    prev = CanonicalRequest(intent="update_profile", missing=[])
    fresh = CanonicalRequest(intent="general_question")
    node = make_parse_request_node(ScriptedCanonical([fresh]))
    state: dict[str, object] = {
        "messages": [HumanMessage(content="مرحبا")],
        "canonical_request": prev,
        "missing_fields": [],
    }
    out = node(state)  # type: ignore[arg-type]
    assert out["canonical_request"].intent == "general_question"  # type: ignore[union-attr]


def test_full_name_sequence_question_then_single_word_then_save() -> None:
    """أريد تغيير اسمي ← سؤال ← بلال ← حفظ."""
    structured = ScriptedProfile([ProfileName(name=None), ProfileName(name="بلال")])
    writer = FakeWriter()
    extract = make_extract_profile_node(structured)  # type: ignore[arg-type]
    save = make_save_profile_node(writer)  # type: ignore[arg-type]

    # الدور 1: بلا اسم مستخرج ← سؤال موسوم.
    turn1: dict[str, object] = {"messages": [HumanMessage(content="أريد تغيير اسمي")]}
    turn1.update(extract(turn1))  # type: ignore[arg-type]
    assert route_after_profile_extract(turn1) == "ask_profile_name"  # type: ignore[arg-type]
    turn1.update(ask_profile_name_node(turn1))  # type: ignore[arg-type]
    assert "name" in list(turn1.get("missing_fields", []))  # type: ignore[union-attr]

    # الدور 2: كلمة واحدة مصنفة غامضة ← تستأنف ← تستخرج ← تحفظ.
    parse = make_parse_request_node(
        ScriptedCanonical([CanonicalRequest(intent="general_question")])
    )
    turn2: dict[str, object] = {
        "messages": [HumanMessage(content="بلال")],
        "canonical_request": CanonicalRequest(intent="update_profile", missing=[]),
        "missing_fields": list(turn1.get("missing_fields", [])),  # type: ignore[union-attr]
        "teacher_id": 7,
    }
    parsed = parse(turn2)  # type: ignore[arg-type]
    assert parsed["canonical_request"].intent == "update_profile"  # type: ignore[union-attr]
    turn2.update(extract(turn2))  # type: ignore[arg-type]
    assert route_after_profile_extract(turn2) == "save_profile"  # type: ignore[arg-type]
    turn2.update(save(turn2))  # type: ignore[arg-type]
    assert writer.saved == ["بلال"]
    assert list(turn2.get("missing_fields", [])) == []
