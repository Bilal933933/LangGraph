"""اختبارات نسخة المعلم واحداث التقدم (بلا توليد)."""

import asyncio
from collections.abc import AsyncIterator
from types import SimpleNamespace
from typing import Any

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.models import User  # noqa: F401 - تسجيل الجداول في Base
from app.core.errors import AppError, ErrorCode
from app.db.engine import dispose_engine
from app.db.models import Base
from app.db.models.conversation import Conversation
from app.db.models.teacher import Teacher  # noqa: F401 - تسجيل الجدول في Base
from app.domain.outputs.quiz import QuizOutput
from app.graph.progress import emit
from app.graph.streaming import stream_run
from app.rendering.registry import render_teacher_copy
from app.services import conversation_service as service


def _quiz_dict() -> dict:
    return {
        "topic": "QT",
        "grade_level": "QG",
        "questions": [
            {
                "type": "mcq",
                "stem": "QS",
                "options": ["A", "B", "C", "D"],
                "answer_index": 1,
                "explanation": "QE",
                "points": 100,
            }
        ],
    }


def _sheet_dict() -> dict:
    return {
        "kind": "worksheet",
        "topic": "WT",
        "grade_level": "WG",
        "items": [{"instruction": "WI", "expected_answer": "WA"}],
    }


def test_teacher_quiz_copy_shows_answers() -> None:
    text = render_teacher_copy({"quiz_draft": QuizOutput.model_validate(_quiz_dict())}, "quiz")
    assert "QS" in text and "QE" in text


def test_teacher_copy_accepts_dict_draft() -> None:
    text = render_teacher_copy({"quiz_draft": _quiz_dict()}, "quiz")
    assert "QE" in text
    sheet = render_teacher_copy({"worksheet_draft": _sheet_dict()}, "worksheet")
    assert "WA" in sheet


def test_teacher_copy_missing_draft_is_not_found() -> None:
    with pytest.raises(AppError) as info:
        render_teacher_copy({}, "quiz")
    assert info.value.code == ErrorCode.NOT_FOUND


def test_teacher_copy_bad_kind_rejected() -> None:
    with pytest.raises(AppError) as info:
        render_teacher_copy({}, "plan")
    assert info.value.code == ErrorCode.VALIDATION_FAILED


def test_emit_outside_stream_never_raises() -> None:
    emit("quiz_agent", "start")
    emit("worksheet_write", "shaping")


class FakeCustomGraph:
    def __init__(self, script: list) -> None:
        self._script = script

    async def astream(
        self, payload: object, config: object = None, *, stream_mode: object = None
    ) -> AsyncIterator:
        _ = (payload, config, stream_mode)
        for item in self._script:
            yield item


def test_custom_mode_forwards_progress() -> None:
    async def _run() -> list:
        graph = FakeCustomGraph([("custom", {"node": "quiz_agent", "phase": "shaping"})])
        return [e async for e in stream_run(graph, {}, {})]

    events = asyncio.run(_run())
    assert events[0] == {"type": "progress", "node": "quiz_agent", "phase": "shaping"}
    assert events[-1]["type"] == "done"


class StubGraph:
    def __init__(self, values: dict) -> None:
        self._values = values

    async def aget_state(self, config: object) -> Any:
        _ = config
        return SimpleNamespace(values=self._values)


def _session() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    user = User(email="t@example.com", password_hash="x")
    sess.add(user)
    sess.commit()
    teacher = service.get_or_create_teacher(sess, user)
    conv = Conversation(teacher_id=teacher.id, title="c")
    sess.add(conv)
    sess.commit()
    sess._engine = engine  # type: ignore[attr-defined]
    return sess


def test_teacher_copy_detail_reads_draft() -> None:
    sess = _session()
    try:
        user = sess.query(User).first()
        assert user is not None
        conv = sess.query(Conversation).first()
        assert conv is not None
        graph = StubGraph({"quiz_draft": _quiz_dict()})
        detail = asyncio.run(service.teacher_copy_detail(sess, graph, user, conv.id, "quiz"))
        assert detail["kind"] == "quiz"
        assert isinstance(detail["text"], str) and "QE" in detail["text"]
    finally:
        engine = sess._engine  # type: ignore[attr-defined]
        sess.close()
        dispose_engine(engine)


def test_teacher_copy_detail_forbidden_is_not_found() -> None:
    sess = _session()
    try:
        user = sess.query(User).first()
        assert user is not None
        with pytest.raises(AppError) as info:
            asyncio.run(service.teacher_copy_detail(sess, StubGraph({}), user, 9999, "quiz"))
        assert info.value.code == ErrorCode.NOT_FOUND
    finally:
        engine = sess._engine  # type: ignore[attr-defined]
        sess.close()
        dispose_engine(engine)

