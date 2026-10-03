"""اختبارات جدولي العمل (sqlite في الذاكرة، بلا Postgres حقيقي)."""

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.db.engine import create_tables, dispose_engine, get_engine
from app.db.models import Question, Quiz


def _session() -> tuple[Session, Engine]:
    engine = get_engine("sqlite:///:memory:")
    create_tables(engine)
    return Session(engine), engine


def test_create_quiz_with_questions() -> None:
    session, engine = _session()
    try:
        quiz = Quiz(topic="الكسور", grade_level="الصف الرابع", num_questions=2, thread_id="t1")
        quiz.questions = [
            Question(qtype="mcq", text="ما البسط؟", options=["1", "2"], answer="1"),
            Question(qtype="tf", text="1/2 نصف.", answer="صح"),
        ]
        session.add(quiz)
        session.commit()
        found = session.get(Quiz, quiz.id)
        assert found is not None and len(found.questions) == 2
    finally:
        session.close()
        dispose_engine(engine)


def test_cascade_deletes_questions() -> None:
    session, engine = _session()
    try:
        quiz = Quiz(topic="الكسور", thread_id="t2")
        quiz.questions = [Question(qtype="mcq", text="س؟")]
        session.add(quiz)
        session.commit()
        session.delete(quiz)
        session.commit()
        assert session.query(Question).count() == 0
    finally:
        session.close()
        dispose_engine(engine)
