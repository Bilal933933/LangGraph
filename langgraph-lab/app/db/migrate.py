"""الترحيل عند الإقلاع (بديل create_all في بيئة التشغيل)."""

from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config

from app.core.errors import AppError, ErrorCode


def _alembic_config(database_url: str) -> Config:
    """DATABASE_URL ← إعداد Alembic جاهز للترقية حتى head."""
    root = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "migrations"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    return cfg


def upgrade_to_head(database_url: str) -> None:
    """يرقّي المخطط حتى head. ينجح بصمت أو يرمي خطأ عربيا صريحا."""
    try:
        upgrade(_alembic_config(database_url), "head")
    except Exception as exc:
        raise AppError(
            ErrorCode.DB_CONNECTION_FAILED,
            "تعذر ترحيل قاعدة البيانات (Alembic). تحقق من DATABASE_URL وأن Postgres يعمل.",
            status=503,
        ) from exc
