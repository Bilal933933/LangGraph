"""الإعدادات (pydantic-settings)."""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """إعدادات التطبيق من متغيرات البيئة."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "langgraph-lab"
    google_api_key: SecretStr = SecretStr("")
    gemini_model: str = "gemini-3.5-flash-lite"
    database_url: SecretStr = SecretStr("")
    jwt_secret: SecretStr = SecretStr("dev-only-secret-change-me-32-chars!")
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 30
    log_level: str = "INFO"
    log_dir: str = "logs"
    plan_retrieval_limit: int = 20
    answer_retrieval_limit: int = 6
    tavily_api_key: SecretStr = SecretStr("")
    web_search_limit: int = 5
    web_timeout_seconds: float = 10.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """إعدادات مخزنة (Singleton بسيط)."""
    return Settings()
