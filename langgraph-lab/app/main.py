"""نقطة دخول FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine

import app.auth.models as _auth_models  # noqa: F401 - تسجيل جداول المصادقة في Base قبل create_all
from app.api.conversations import router as conversations_router
from app.api.routes import close_checkpointer, router
from app.api.streams import router as streams_router
from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.errors.handlers import register_error_handlers
from app.core.trace import setup_logging
from app.db.engine import check_connection, dispose_engine, get_engine
from app.db.knowledge_indexes import ensure_knowledge_indexes, ensure_vector_extensions
from app.db.migrate import upgrade_to_head
from app.graph.checkpoints import setup_postgres_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """بدء ← ترحيل Alembic + جداول لقطات LangGraph، إيقاف ← إغلاق نظيف."""
    settings = get_settings()
    setup_logging(log_dir=settings.log_dir, level=settings.log_level)
    database_url = settings.database_url.get_secret_value().strip()
    engine: Engine | None = None
    if database_url:
        engine = get_engine(database_url)
        check_connection(engine)
        ensure_vector_extensions(engine)
        upgrade_to_head(database_url)
        ensure_knowledge_indexes(engine)
        setup_postgres_tables(database_url)
        app.state.db_engine = engine
    yield
    close_checkpointer()
    if engine is not None:
        dispose_engine(engine)


def create_app() -> FastAPI:
    """تبني التطبيق: الإعدادات + الأخطاء + المسارات."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    # السماح للواجهة فقط بمناداة API من المتصفح (تضبط عبر CORS_ORIGINS).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(router)
    app.include_router(streams_router)
    app.include_router(conversations_router)
    app.include_router(auth_router)
    return app


app = create_app()
