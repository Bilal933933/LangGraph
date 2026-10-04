"""تطبيق التشفير والتوكنات (تفاصيل تقنية فقط، بلا قرارات عمل)."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt


def hash_password(password: str) -> str:
    """كلمة سر خام ← هاش bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """مقارنة آمنة ضد التوقيت."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def issue_access_token(user_id: int, secret: str, ttl_minutes: int) -> str:
    """معرف المستخدم ← JWT قصير العمر."""
    now = datetime.now(UTC)
    payload = {"sub": str(user_id), "iat": now, "exp": now + timedelta(minutes=ttl_minutes)}
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> int:
    """توكن ← معرف المستخدم، يرمي ValueError عند أي عطل."""
    payload = jwt.decode(token, secret, algorithms=["HS256"])
    return int(payload["sub"])


def generate_refresh_token() -> tuple[str, str]:
    """ينتج (الخام للعميل، الهاش للتخزين). الخام لا يُخزن أبدًا."""
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, digest


def hash_refresh_token(raw: str) -> str:
    """خام التوكن ← بصمته للمقارنة في DB."""
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
