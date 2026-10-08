"""اختبارات مسار الملف الشخصي: استخراج الاسم + حفظه بالهوية من الحالة."""

from collections.abc import AsyncIterator
from typing import Any, TypeVar, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from app.domain.models import Intent, IntentResult, ProfileInfo, ProfileName
from app.domain.ports import ChatModelPort
from app.graph.builder import build_graph
from app.graph.edges import route_after_profile_extract, route_by_request
from app.services.chat_service import ChatService

T = TypeVar("T", bound=BaseModel)


class FakeChat:
    """نموذج نصي وهمي (لا يستخدم في مسار الملف، لكن البناء يتطلبه)."""

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        return AIMessage(content="fake")

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = (messages, callbacks)
        yield "fake"

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


class FakeStructuredProfile:
    """منفذ مهيكل وهمي: نية update_profile واسم قابل للضبط."""

    def __init__(self, profile: str | None = "أحمد") -> None:
        self._profile = profile

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = messages
        if schema is IntentResult:
            return cast("T", IntentResult(intent="update_profile"))
        if schema is ProfileName:
            return cast("T", ProfileName(name=self._profile))
        if schema is ProfileInfo:
            return cast("T", ProfileInfo(name=self._profile))
        raise AssertionError(f"unexpected schema {schema}")


class DictWriter:
    """كاتب وهمي في الذاكرة."""

    def __init__(self) -> None:
        self.saved: dict[int, str] = {}

    def get_name(self, teacher_id: int) -> str | None:
        return self.saved.get(teacher_id)

    def update_name(self, teacher_id: int, name: str) -> str:
        self.saved[teacher_id] = name.strip()
        return self.saved[teacher_id]


def _service(profile: str | None, writer: DictWriter) -> ChatService:
    graph = build_graph(FakeChat(), FakeStructuredProfile(profile), [], profile_writer=writer)
    return ChatService(graph)


def test_update_profile_saves_name() -> None:
    writer = DictWriter()
    reply = _service("أحمد", writer).handle_message("أنا أحمد", teacher_id=5)
    assert "أحمد" in reply
    assert "سجلت" not in reply
    assert writer.saved[5] == "أحمد"


def test_update_profile_no_name_asks() -> None:
    writer = DictWriter()
    reply = _service(None, writer).handle_message("أهلا", teacher_id=5)
    assert "ما الاسم" in reply
    assert writer.saved == {}


def test_update_profile_guest_needs_login() -> None:
    writer = DictWriter()
    reply = _service("أحمد", writer).handle_message("أنا أحمد")
    assert "سجل الدخول" in reply
    assert writer.saved == {}


def test_profile_routes() -> None:
    assert (
        route_by_request({"messages": [], "intent": "update_profile"}) == "extract_profile"
    )
    assert (
        route_after_profile_extract({"messages": [], "pending_profile_name": "أحمد"})
        == "save_profile"
    )
    assert (
        route_after_profile_extract({"messages": [], "pending_profile_name": None})
        == "ask_profile_name"
    )
    assert route_after_profile_extract({"messages": []}) == "ask_profile_name"


def test_sql_writer_roundtrip(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy.orm import Session

    from app.auth.models import User  # noqa: F401
    from app.db.engine import dispose_engine, get_engine
    from app.db.models import Base
    from app.db.models.teacher import Teacher
    from app.repositories.sql_teacher import SqlTeacherDirectory

    url = f"sqlite:///{tmp_path}/profile.db"
    engine = get_engine(url)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(Teacher(id=7, name="", email="t7@x.io"))
            session.commit()
        directory = SqlTeacherDirectory(url)
        assert directory.update_name(7, "  سارة  ") == "سارة"
        assert directory.get_name(7) == "سارة"
    finally:
        dispose_engine(engine)


def test_intent_type_includes_update_profile() -> None:
    intent: Intent = "update_profile"
    assert intent == "update_profile"


class FakeAnswer:
    """نموذج إجابة وهمي للمسار الاستنتاجي."""

    def __init__(self, text: str = "شرح الكسور هنا") -> None:
        self._text = text

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        _ = messages
        return AIMessage(content=self._text)

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = (messages, callbacks)
        yield self._text

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


class FakeStructuredInfer:
    """نية عامة + ملف مستنتج قابل للضبط."""

    def __init__(self, info: ProfileInfo) -> None:
        self._info = info

    def parse(self, messages: list[BaseMessage], schema: type[T]) -> T:
        _ = messages
        if schema is IntentResult:
            return cast("T", IntentResult(intent="general_question"))
        if schema is ProfileInfo:
            return cast("T", self._info)
        raise AssertionError(f"unexpected schema {schema}")


class DictProfileStore:
    """مخزن ملف وهمي في الذاكرة (الصفوف اتحادا)."""

    def __init__(self, initial: dict[str, object] | None = None) -> None:
        self.data: dict[str, object] = {"name": "", "subject": "", "grades": []}
        if initial:
            self.data.update(initial)

    def load_profile(self, teacher_id: int) -> dict[str, object]:
        _ = teacher_id
        grades = list(self.data["grades"])  # type: ignore[arg-type]
        return {"name": self.data["name"], "subject": self.data["subject"], "grades": grades}

    def save_profile(self, teacher_id: int, patch: dict[str, object]) -> dict[str, object]:
        _ = teacher_id
        for key in ("name", "subject"):
            value = patch.get(key)
            if isinstance(value, str) and value.strip():
                self.data[key] = value.strip()
        grades = patch.get("grades")
        if isinstance(grades, list):
            merged = list(self.data["grades"])  # type: ignore[arg-type]
            for raw in grades:
                if isinstance(raw, str) and raw.strip() and raw.strip() not in merged:
                    merged.append(raw.strip())
            self.data["grades"] = merged
        return self.load_profile(teacher_id)


class RecordingAnswer:
    """نموذج إجابة يسجل الموجه الوارد (لإثبات حقن تعليم السؤال)."""

    def __init__(self, text: str = "شرح الكسور هنا") -> None:
        self._text = text
        self.seen: list[BaseMessage] = []

    def invoke(self, messages: list[BaseMessage], callbacks: Any = None) -> AIMessage:
        self.seen = list(messages)
        return AIMessage(content=self._text)

    async def astream(
        self, messages: list[BaseMessage], callbacks: Any = None
    ) -> AsyncIterator[str]:
        _ = callbacks
        self.seen = list(messages)
        yield self._text

    def bind_tools(self, tools: list[BaseTool]) -> ChatModelPort:
        _ = tools
        return self


def _prompt_text(model: RecordingAnswer) -> str:
    from app.graph.content import message_text

    return "\n".join(message_text(m.content) for m in model.seen)


def _infer_service(info: ProfileInfo, store: DictProfileStore) -> ChatService:
    graph = build_graph(FakeAnswer(), FakeStructuredInfer(info), [], profile_store=store)
    return ChatService(graph)


def _recording_service(
    info: ProfileInfo, store: DictProfileStore
) -> tuple[ChatService, RecordingAnswer]:
    model = RecordingAnswer()
    graph = build_graph(model, FakeStructuredInfer(info), [], profile_store=store)
    return ChatService(graph), model


def test_infer_saves_silently_and_model_asks() -> None:
    store = DictProfileStore()
    service, model = _recording_service(ProfileInfo(name="أحمد"), store)
    reply = service.handle_message("أنا أحمد، اشرح لي الكسور", teacher_id=5)
    assert reply == "شرح الكسور هنا"
    assert store.data["name"] == "أحمد"
    assert "مادة تخصصك" in _prompt_text(model)
    assert "تم يا" not in reply
    assert "سجلت" not in reply


def test_complete_profile_no_instruction() -> None:
    store = DictProfileStore({"name": "سارة", "subject": "الرياضيات", "grades": ["الرابع"]})
    service, model = _recording_service(ProfileInfo(name="سارة"), store)
    reply = service.handle_message("اشرح لي الكسور", teacher_id=5)
    assert reply == "شرح الكسور هنا"
    assert "مادة تخصصك" not in _prompt_text(model)


def test_never_overwrites_filled_name() -> None:
    store = DictProfileStore({"name": "سارة"})
    service, model = _recording_service(ProfileInfo(name="أحمد"), store)
    reply = service.handle_message("أنا أحمد", teacher_id=5)
    assert store.data["name"] == "سارة"
    assert reply == "شرح الكسور هنا"
    assert "مادة تخصصك" in _prompt_text(model)


def test_no_store_keeps_old_behavior() -> None:
    graph = build_graph(FakeAnswer(), FakeStructuredInfer(ProfileInfo(name="أحمد")), [])
    reply = ChatService(graph).handle_message("أنا أحمد، اشرح لي الكسور", teacher_id=5)
    assert reply == "شرح الكسور هنا"


def test_grades_merge_without_duplicates() -> None:
    store = DictProfileStore({"name": "أحمد", "grades": ["الأول"]})
    info = ProfileInfo(grades=["الأول", "الثاني الإعدادي"])
    service, model = _recording_service(info, store)
    reply = service.handle_message("أدرس الأول والثاني الإعدادي", teacher_id=5)
    assert store.data["grades"] == ["الأول", "الثاني الإعدادي"]
    assert reply == "شرح الكسور هنا"
    assert "مادة تخصصك" in _prompt_text(model)


def test_asks_grades_in_plural() -> None:
    store = DictProfileStore({"name": "أحمد", "subject": "الرياضيات"})
    service, model = _recording_service(ProfileInfo(name="أحمد"), store)
    service.handle_message("أنا أحمد", teacher_id=5)
    assert "صفوف" in _prompt_text(model)


def test_sql_profile_grades_merge(tmp_path) -> None:  # type: ignore[no-untyped-def]
    from sqlalchemy.orm import Session

    from app.auth.models import User  # noqa: F401
    from app.db.engine import dispose_engine, get_engine
    from app.db.models import Base
    from app.db.models.teacher import Teacher, TeacherGrade
    from app.repositories.sql_teacher import SqlTeacherProfile

    url = f"sqlite:///{tmp_path}/grades.db"
    engine = get_engine(url)
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add(Teacher(id=9, name="", email="t9@x.io"))
            session.add(TeacherGrade(teacher_id=9, grade="الأول"))
            session.commit()
        store = SqlTeacherProfile(url)
        assert store.load_profile(9)["grades"] == ["الأول"]
        snapshot = store.save_profile(9, {"grades": ["الأول", "الثاني"]})
        assert snapshot["grades"] == ["الأول", "الثاني"]
    finally:
        dispose_engine(engine)
