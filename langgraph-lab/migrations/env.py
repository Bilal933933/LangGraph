"""بيئة Alembic: DATABASE_URL ← ترحيل نسخي لجداول التطبيق."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

import app.auth.models as _auth_models  # noqa: F401 - تسجيل users قبل الترحيل
import app.db.models as _models  # noqa: F401 - تسجيل knowledge_chunks
from app.db.models.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """رابط DB من Alembic config أو متغيرات البيئة."""
    url = config.get_main_option("sqlalchemy.url") or os.getenv("DATABASE_URL", "")
    return url.strip().strip("\"'")


def run_migrations_offline() -> None:
    """وضع offline: SQL نصي بلا اتصال (للمراجعة فقط)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """وضع online: اتصال فعلي ثم ترحيل."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
