"""جدول المعلم (مالك المحادثات)."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.models.base import Base

if TYPE_CHECKING:
    from app.auth.models import User
    from app.db.models.conversation import Conversation


class Teacher(Base):
    """معلم واحد: مرتبط بحساب User واحد ومالك لمحادثاته."""

    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True, default=None
    )
    name: Mapped[str] = mapped_column(String(100), default="")
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, default="")
    subject: Mapped[str | None] = mapped_column(String(100), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User | None"] = relationship(back_populates="teacher", uselist=False)
    grades: Mapped[list["TeacherGrade"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="teacher", cascade="all, delete-orphan"
    )


class TeacherGrade(Base):
    """صف واحد يدرسه المعلم (صفوف متعددة = صفوف متعددة)."""

    __tablename__ = "teacher_grades"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id", ondelete="CASCADE"), index=True
    )
    grade: Mapped[str] = mapped_column(String(100))

    teacher: Mapped["Teacher"] = relationship(back_populates="grades")
