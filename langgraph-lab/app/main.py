"""نقطة دخول FastAPI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.engine import Engine

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors.handlers import register_error_handlers
from app.db.engine import check_connection, create_tables, dispose_engine, get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """بدء ← فحص اتصال وإنشاء جدولي العمل، إيقاف ← إغلاق نظيف."""
    database_url = get_settings().database_url.get_secret_value().strip()
    engine: Engine | None = None
    if database_url:
        engine = get_engine(database_url)
        check_connection(engine)
        create_tables(engine)
        app.state.db_engine = engine
    yield
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
    return app


app = create_app()
