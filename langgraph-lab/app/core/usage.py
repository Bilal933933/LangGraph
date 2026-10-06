"""محاسبة الرموز اليومية: جامع callbacks + تجميع DB (وظيفة واحدة)."""

from datetime import UTC, date, datetime
from typing import Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage
from langchain_core.outputs import LLMResult
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.core.trace import get_logger
from app.db.models.token_usage import TokenUsage

logger = get_logger(__name__)


def today_utc() -> date:
    """اليوم الحالي بتوقيت UTC (مفتاح التجميع)."""
    return datetime.now(UTC).date()


def subject_for_user(user_id: int) -> str:
    """مستخدم ← مفتاح تجميع."""
    return f"user:{user_id}"


def subject_for_ip(ip: str) -> str:
    """IP ← مفتاح تجميع للضيوف."""
    return f"ip:{ip.strip() or 'unknown'}"


def _tokens_from_message(message: BaseMessage) -> tuple[int, int]:
    """رسالة ← (دخل، خرج).

    الأولوية للصيغة القياسية `usage_metadata` (تضعها langchain-google-genai
    كـ input_tokens/output_tokens)، ثم الاحتياطي القديم داخل
    `response_metadata["usage_metadata"]` (prompt_token_count/candidates_token_count).
    """
    raw_standard = getattr(message, "usage_metadata", None)
    if isinstance(raw_standard, dict):
        prompt = int(raw_standard.get("input_tokens") or 0)
        completion = int(raw_standard.get("output_tokens") or 0)
        if prompt or completion:
            return (prompt, completion)
    raw = (message.response_metadata or {}).get("usage_metadata")
    if isinstance(raw, dict):
        prompt = int(raw.get("prompt_token_count") or 0)
        completion = int(raw.get("candidates_token_count") or 0)
        return (prompt, completion)
    return (0, 0)


class UsageCollector(BaseCallbackHandler):
    """يجمع prompt/candidates من usage_metadata القياسي أولًا (يسقط للمسارات القديمة)."""

    def __init__(self) -> None:
        super().__init__()
        self.input_tokens = 0
        self.output_tokens = 0

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        _ = kwargs
        found = False
        for flat in response.generations:
            for generation in flat:
                message = getattr(generation, "message", None)
                prompt, completion = (0, 0)
                if isinstance(message, BaseMessage):
                    prompt, completion = _tokens_from_message(message)
                if prompt or completion:
                    found = True
                self.input_tokens += prompt
                self.output_tokens += completion
        if not found:
            usage = (response.llm_output or {}).get("token_usage") or {}
            if isinstance(usage, dict):
                self.input_tokens += int(usage.get("prompt_tokens") or 0)
                self.output_tokens += int(usage.get("completion_tokens") or 0)

    @property
    def total(self) -> int:
        """مجموع الرموز الملتقطة في هذا الطلب."""
        return self.input_tokens + self.output_tokens


def record_usage(
    session: Session,
    subject: str,
    input_tokens: int,
    output_tokens: int,
    day: date | None = None,
) -> None:
    """يضيف رموزًا لتجميع اليوم عبر upsert ذري.

    يستخدم INSERT … ON CONFLICT DO UPDATE فلا تتعارض الطلبات المتزامنة.
    الكتابة في savepoint فقط: الفشل يُسجَّل كتحذير ولا يُسقط الجلسة
    الأصلية (الميزانية تُرفع لا تُسقط الطلب ولا رسائل المحادثة).
    """
    target = day or today_utc()
    in_tokens = max(0, int(input_tokens))
    out_tokens = max(0, int(output_tokens))
    try:
        bind = session.get_bind()
        dialect = bind.dialect.name if bind is not None else ""
        values = {
            "subject": subject,
            "day": target,
            "input_tokens": in_tokens,
            "output_tokens": out_tokens,
        }
        if dialect == "postgresql":
            stmt: Any = pg_insert(TokenUsage).values(**values)
        else:
            stmt = sqlite_insert(TokenUsage).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["subject", "day"],
            set_={
                "input_tokens": TokenUsage.input_tokens + in_tokens,
                "output_tokens": TokenUsage.output_tokens + out_tokens,
            },
        )
        with session.begin_nested():
            session.execute(stmt)
        session.flush()
    except Exception as exc:
        logger.warning("token_usage_record_failed subject=%r error=%r", subject, exc)


def get_today_usage(
    session: Session, subject: str, day: date | None = None
) -> tuple[int, int]:
    """مفتاح ← (دخل، خرج) اليوم أو (0, 0). DB متعثرة ← (0, 0) مع تحذير."""
    target = day or today_utc()
    try:
        row = (
            session.query(TokenUsage)
            .filter(TokenUsage.subject == subject, TokenUsage.day == target)
            .first()
        )
    except Exception as exc:
        logger.warning("token_usage_read_failed subject=%r error=%r", subject, exc)
        return (0, 0)
    if row is None:
        return (0, 0)
    return (int(row.input_tokens), int(row.output_tokens))
