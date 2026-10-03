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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """إعدادات مخزنة (Singleton بسيط)."""
    return Settings()
