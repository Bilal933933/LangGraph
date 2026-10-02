"""نقطة دخول FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.errors.handlers import register_error_handlers


def create_app() -> FastAPI:
    """تبني التطبيق: الإعدادات + الأخطاء + المسارات."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
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
