"""جدول طلب الاختبار (منقول كما هو)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.db.models.question import Question


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
