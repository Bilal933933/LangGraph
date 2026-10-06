"""تجميع الرموز اليومي لكل subject (مستخدم أو IP ضيف)."""

from datetime import date

from sqlalchemy import Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class TokenUsage(Base):
    """صف واحد لكل (subject, day): مجموع الدخل والخرج."""

    __tablename__ = "token_usage"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(128), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)

    __table_args__ = (
        UniqueConstraint("subject", "day", name="uq_token_usage_subject_day"),
    )
