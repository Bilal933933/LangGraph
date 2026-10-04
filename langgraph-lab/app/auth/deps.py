"""اعتماديات FastAPI للمصادقة (جلسة DB + المستخدم الحالي)."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import security
from app.auth.models import User
from app.auth.repository import SqlAuthRepository
from app.core.config import get_settings
from app.core.errors import AppError, ErrorCode
from app.db.engine import get_engine

_bearer = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    """جلسة SQLAlchemy واحدة لكل طلب."""
    url = get_settings().database_url.get_secret_value().strip()
    engine = get_engine(url or "sqlite:///:memory:")
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        engine.dispose()


def get_repo(session: Annotated[Session, Depends(get_db)]) -> SqlAuthRepository:
    """مستودع واحد لكل طلب."""
    return SqlAuthRepository(session)


def get_current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    session: Annotated[Session, Depends(get_db)],
) -> User:
    """يستخرج Bearer ← يفك access ← يجلب المستخدم النشط."""
    _ = request
    if creds is None or not creds.credentials:
        raise AppError(ErrorCode.UNAUTHORIZED, "يلزم تسجيل الدخول.", status=401)
    try:
        user_id = security.decode_access_token(
            creds.credentials, get_settings().jwt_secret.get_secret_value()
        )
    except Exception as exc:
        raise AppError(ErrorCode.TOKEN_INVALID, "توكن غير صالح.", status=401) from exc
    user = SqlAuthRepository(session).find_user_by_id(user_id)
    if user is None or not user.is_active:
        raise AppError(ErrorCode.UNAUTHORIZED, "يلزم تسجيل الدخول.", status=401)
    return user
