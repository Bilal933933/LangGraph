"""محدد المعدل (نافذة منزلقة لكل مفتاح في ذاكرة العملية)."""

import math
import time
from collections import deque
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, get_db
from app.auth.models import User
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.core.usage import get_today_usage, subject_for_ip, subject_for_user

#: نافذة القياس الواحدة (ثانية).
_WINDOW_SECONDS = 60.0

_hits: dict[str, deque[float]] = {}


def reset_rate_limits() -> None:
    """يصفر النوافذ (للاختبارات فقط)."""
    _hits.clear()


def check_rate(key: str, limit: int, window: float, now: float | None = None) -> float:
    """مفتاح ← 0 مسموح، أو ثواني الانتظار. now للحقن في الاختبارات."""
    current = time.monotonic() if now is None else now
    hits = _hits.setdefault(key, deque())
    while hits and hits[0] <= current - window:
        hits.popleft()
    if len(hits) >= limit:
        return max(0.0, hits[0] + window - current)
    hits.append(current)
    return 0.0


def enforce_rate(key: str, limit: int, window: float, now: float | None = None) -> None:
    """يفحص ويرمي 429 مع مدة الانتظار عند التجاوز."""
    wait = check_rate(key, limit, window, now)
    if wait > 0.0:
        raise AppError(
            ErrorCode.RATE_LIMITED,
            f"طلبات كثيرة. حاول بعد {math.ceil(wait)} ثانية.",
            status=429,
            details={"retry_after": math.ceil(wait)},
        )


def client_ip(request: Request) -> str:
    """الطلب ← IP العميل المباشر (خلف وكيل يُوثق لاحقًا)."""
    return request.client.host if request.client is not None else "unknown"


def check_budget(session: Session, subject: str, cap: int) -> None:
    """سقف الرموز اليومي ← رفض 429 قبل إنفاق أي رمز (0 = بلا سقف)."""
    if cap <= 0:
        return
    used_in, used_out = get_today_usage(session, subject)
    if used_in + used_out >= cap:
        raise AppError(
            ErrorCode.TOKEN_BUDGET_EXCEEDED,
            "بلغت حد الرموز اليومي. يعود غدًا.",
            status=429,
            details={"cap": cap, "used": used_in + used_out},
        )


def limit_auth_request(request: Request) -> None:
    """بوابة المصادقة: حد صارم لكل IP (ضد التخمين)."""
    enforce_rate(f"auth:{client_ip(request)}", get_settings().auth_rpm, _WINDOW_SECONDS)


def limit_guest_chat(request: Request, session: Annotated[Session, Depends(get_db)]) -> None:
    """دردشة الضيوف: حد لكل IP + سقف رموز يومي."""
    settings = get_settings()
    enforce_rate(
        f"chat:guest:{client_ip(request)}", settings.chat_guest_rpm, _WINDOW_SECONDS
    )
    check_budget(session, subject_for_ip(client_ip(request)), settings.daily_token_cap)


def limit_user_chat(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> None:
    """دردشة المسجلين: حد لكل مستخدم + سقف رموز يومي."""
    _ = request
    settings = get_settings()
    enforce_rate(f"chat:user:{user.id}", settings.chat_rpm, _WINDOW_SECONDS)
    check_budget(session, subject_for_user(user.id), settings.daily_token_cap)
