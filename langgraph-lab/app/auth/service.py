"""منطق المصادقة (كل القرارات هنا، بلا HTTP ولا SQL مباشر)."""

from datetime import UTC, datetime, timedelta

from app.auth import security
from app.auth.policy import assert_strong_password, normalize_email
from app.auth.repository import SqlAuthRepository
from app.core.errors import AppError, ErrorCode


class TokenPair:
    """حامل التوكنين (يحوله الراوتر إلى Pydantic)."""

    def __init__(self, access_token: str, refresh_token: str) -> None:
        self.access_token = access_token
        self.refresh_token = refresh_token


class AuthService:
    """منسق المصادقة: سياسة ← مستودع ← تشفير."""

    def __init__(
        self, repo: SqlAuthRepository, jwt_secret: str, access_ttl: int, refresh_days: int
    ) -> None:
        self._repo = repo
        self._secret = jwt_secret
        self._access_ttl = access_ttl
        self._refresh_days = refresh_days

    def _issue_pair(self, user_id: int) -> TokenPair:
        access = security.issue_access_token(user_id, self._secret, self._access_ttl)
        raw, digest = security.generate_refresh_token()
        expires = datetime.now(UTC) + timedelta(days=self._refresh_days)
        self._repo.save_session(user_id, digest, expires)
        return TokenPair(access, raw)

    def register(self, email: str, password: str) -> TokenPair:
        """بريد + سر ← توكنان. مكرر البريد = 409."""
        cleaned = normalize_email(email)
        assert_strong_password(password)
        if self._repo.find_user_by_email(cleaned) is not None:
            raise AppError(ErrorCode.EMAIL_TAKEN, "هذا البريد مسجل مسبقًا.", status=409)
        user = self._repo.create_user(cleaned, security.hash_password(password))
        return self._issue_pair(user.id)

    def login(self, email: str, password: str) -> TokenPair:
        """تحقق موحد: نفس الخطأ للبريد والسر (منع التعداد)."""
        cleaned = normalize_email(email)
        user = self._repo.find_user_by_email(cleaned)
        if user is None or not user.is_active:
            raise AppError(ErrorCode.INVALID_CREDENTIALS, "بيانات الدخول غير صحيحة.", status=401)
        if not security.verify_password(password, user.password_hash):
            raise AppError(ErrorCode.INVALID_CREDENTIALS, "بيانات الدخول غير صحيحة.", status=401)
        return self._issue_pair(user.id)

    def refresh(self, raw_refresh: str) -> TokenPair:
        """تدوير: القديم يُلغى دائمًا ويُصدر جديد (كشف إعادة الاستخدام)."""
        digest = security.hash_refresh_token(raw_refresh.strip())
        session = self._repo.find_session_by_hash(digest)
        now = datetime.now(UTC)
        expires = session.expires_at if session else None
        if expires is not None and expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if session is None or session.revoked or expires is None or expires < now:
            if session is not None and not session.revoked:
                self._repo.revoke_all_user_sessions(session.user_id)
            raise AppError(ErrorCode.TOKEN_INVALID, "جلسة غير صالحة، سجل الدخول مجددًا.", status=401)
        user_id = session.user_id
        self._repo.revoke_session(session)
        return self._issue_pair(user_id)

    def logout(self, raw_refresh: str) -> None:
        """يلغي جلسة واحدة (خروج مفرد). خام غير معروف = نجاح صامت."""
        session = self._repo.find_session_by_hash(security.hash_refresh_token(raw_refresh.strip()))
        if session is not None and not session.revoked:
            self._repo.revoke_session(session)

    def logout_all(self, user_id: int) -> None:
        """يلغي كل الجلسات (خروج كلي)."""
        self._repo.revoke_all_user_sessions(user_id)
