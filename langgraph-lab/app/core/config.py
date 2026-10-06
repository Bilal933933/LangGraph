"""الإعدادات (pydantic-settings)."""

import json
from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """إعدادات التطبيق من متغيرات البيئة."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "langgraph-lab"
    google_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.5-flash-lite"
    database_url: SecretStr = SecretStr("")
    jwt_secret: SecretStr = SecretStr("dev-only-secret-change-me-32-chars!")
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 30
    log_level: str = "INFO"
    log_dir: str = "logs"
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    plan_retrieval_limit: int = 20
    answer_retrieval_limit: int = 6
    tavily_api_key: SecretStr = SecretStr("")
    web_search_limit: int = 5
    web_timeout_seconds: float = 10.0
    chat_rpm: int = 30
    chat_guest_rpm: int = 10
    auth_rpm: int = 10
    daily_token_cap: int = 0

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """يقبل JSON أو سلسلة مفصولة بفواصل من CORS_ORIGINS."""
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [o.strip() for o in text.split(",") if o.strip()]
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """إعدادات مخزنة (Singleton بسيط)."""
    return Settings()
