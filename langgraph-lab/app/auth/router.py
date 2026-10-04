"""مسارات المصادقة (HTTP فقط، المنطق في service)."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.auth.deps import get_current_user, get_repo
from app.auth.models import User
from app.auth.repository import SqlAuthRepository
from app.auth.schemas import LoginIn, MeOut, RefreshIn, RegisterIn, TokenPairOut
from app.auth.service import AuthService
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _service(repo: SqlAuthRepository) -> AuthService:
    settings = get_settings()
    return AuthService(
        repo,
        settings.jwt_secret.get_secret_value(),
        settings.jwt_access_minutes,
        settings.jwt_refresh_days,
    )


@router.post("/register", response_model=TokenPairOut, status_code=status.HTTP_201_CREATED)
def post_register(
    payload: RegisterIn, repo: Annotated[SqlAuthRepository, Depends(get_repo)]
) -> TokenPairOut:
    """تسجيل مستخدم جديد ← توكنان."""
    pair = _service(repo).register(payload.email, payload.password)
    return TokenPairOut(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/login", response_model=TokenPairOut)
def post_login(
    payload: LoginIn, repo: Annotated[SqlAuthRepository, Depends(get_repo)]
) -> TokenPairOut:
    """دخول ← توكنان جديدان."""
    pair = _service(repo).login(payload.email, payload.password)
    return TokenPairOut(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenPairOut)
def post_refresh(
    payload: RefreshIn, repo: Annotated[SqlAuthRepository, Depends(get_repo)]
) -> TokenPairOut:
    """تدوير refresh ← زوج جديد، القديم يُلغى."""
    pair = _service(repo).refresh(payload.refresh_token)
    return TokenPairOut(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def post_logout(payload: RefreshIn, repo: Annotated[SqlAuthRepository, Depends(get_repo)]) -> None:
    """خروج مفرد: يلغي الجلسة الممررة."""
    _service(repo).logout(payload.refresh_token)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def post_logout_all(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[SqlAuthRepository, Depends(get_repo)],
) -> None:
    """خروج كلي: يلغي كل الجلسات."""
    _service(repo).logout_all(user.id)


@router.get("/me", response_model=MeOut)
def get_me(user: Annotated[User, Depends(get_current_user)]) -> MeOut:
    """المستخدم الحالي من التوكن."""
    return MeOut(id=user.id, email=user.email)
