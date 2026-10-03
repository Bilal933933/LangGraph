"""جداول العمل (Quiz وQuestion فقط، بلا جداول لقطات)."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """أساس نماذج SQLAlchemy بنمط 2.0 المعلن."""


class Quiz(Base):
    """طلب اختبار واحد: موضوعه وحالته وموافقته وخيطه."""

    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    thread_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    topic: Mapped[str] = mapped_column(String(255))
    grade_level: Mapped[str] = mapped_column(String(64), default="")
    num_questions: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    approved: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    questions: Mapped[list["Question"]] = relationship(
        back_populates="quiz", cascade="all, delete-orphan"
    )


class Question(Base):
    """سؤال واحد مرتبط باختباره."""

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), index=True)
    qtype: Mapped[str] = mapped_column(String(32), default="")
    text: Mapped[str] = mapped_column(Text, default="")
    options: Mapped[list[str]] = mapped_column(JSON, default=list)
    answer: Mapped[str] = mapped_column(Text, default="")
    difficulty: Mapped[str] = mapped_column(String(32), default="")

    quiz: Mapped["Quiz"] = relationship(back_populates="questions")
