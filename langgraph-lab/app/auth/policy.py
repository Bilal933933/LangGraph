"""سياسة المصادقة (قواعد النطاق فقط، بلا تشفير ولا DB)."""

from app.core.errors import AppError, ErrorCode


def normalize_email(email: str) -> str:
    """بريد خام ← بريد موحد للمقارنة والتخزين."""
    cleaned = email.strip().lower()
    if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
        raise AppError(ErrorCode.VALIDATION_FAILED, "البريد الإلكتروني غير صالح.", status=422)
    if len(cleaned) > 255:
        raise AppError(ErrorCode.VALIDATION_FAILED, "البريد طويل جدًا.", status=422)
    return cleaned


def assert_strong_password(password: str) -> None:
    """يفحص قوة كلمة السر، يرمي خطأ عند المخالفة."""
    if len(password) < 8 or len(password) > 128:
        raise AppError(
            ErrorCode.VALIDATION_FAILED, "كلمة السر يجب أن تكون 8 أحرف على الأقل.", status=422
        )
