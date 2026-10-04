"""وصول DB للمصادقة (SQLAlchemy فقط، بلا منطق عمل)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import RefreshSession, User


class SqlAuthRepository:
    """مستودع واحد للمستخدمين والجلسات."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def find_user_by_email(self, email: str) -> User | None:
        """بريد موحد ← المستخدم أو None."""
        return self._session.scalar(select(User).where(User.email == email))

    def find_user_by_id(self, user_id: int) -> User | None:
        """معرف ← المستخدم أو None."""
        return self._session.get(User, user_id)

    def create_user(self, email: str, password_hash: str) -> User:
        """ينشئ مستخدمًا نشطًا ويعيده (بلا commit منفرد، يلتزم به المتصل)."""
        user = User(email=email, password_hash=password_hash, is_active=True)
        self._session.add(user)
        self._session.flush()
        return user

    def save_session(self, user_id: int, token_hash: str, expires_at: datetime) -> RefreshSession:
        """يحفظ جلسة جديدة ويعيدها."""
        session = RefreshSession(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        self._session.add(session)
        self._session.flush()
        return session

    def find_session_by_hash(self, token_hash: str) -> RefreshSession | None:
        """بصمة التوكن ← الجلسة أو None."""
        return self._session.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )

    def revoke_session(self, session: RefreshSession) -> None:
        """يلغي جلسة واحدة."""
        session.revoked = True
        self._session.flush()

    def revoke_all_user_sessions(self, user_id: int) -> None:
        """يلغي كل جلسات المستخدم (تسجيل خروج كلي)."""
        rows = self._session.scalars(
            select(RefreshSession).where(
                RefreshSession.user_id == user_id, RefreshSession.revoked.is_(False)
            )
        ).all()
        for row in rows:
            row.revoked = True
        self._session.flush()
