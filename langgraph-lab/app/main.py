"""نقطة دخول FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine

import app.auth.models as _auth_models  # noqa: F401 - تسجيل جداول المصادقة في Base قبل create_all
from app.api.conversations import router as conversations_router
from app.api.routes import close_checkpointer, router
from app.auth.router import router as auth_router
from app.core.config import get_settings
from app.core.errors.handlers import register_error_handlers
from app.db.engine import check_connection, create_tables, dispose_engine, get_engine
from app.graph.checkpoints import setup_postgres_tables


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """بدء ← جداول التطبيق + جداول لقطات LangGraph، إيقاف ← إغلاق نظيف."""
    database_url = get_settings().database_url.get_secret_value().strip()
    engine: Engine | None = None
    if database_url:
        engine = get_engine(database_url)
        check_connection(engine)
        create_tables(engine)
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
    # السماح للواجهة (مجلد frontend) بمناداة API من المتصفح.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(router)
    app.include_router(conversations_router)
    app.include_router(auth_router)
    return app


app = create_app()
