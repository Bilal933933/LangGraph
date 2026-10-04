"""نماذج الدخل/الخرج للمصادقة (Pydantic = تحقق صارم)."""

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    """جسم POST /auth/register."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    """جسم POST /auth/login."""

    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=128)


class RefreshIn(BaseModel):
    """جسم POST /auth/refresh."""

    refresh_token: str = Field(min_length=10, max_length=512)


class TokenPairOut(BaseModel):
    """توكنان للعميل."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    """المستخدم الحالي."""

    id: int
    email: str
