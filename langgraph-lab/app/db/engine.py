"""الاتصال بقاعدة البيانات وإنشاء جداول العمل (اتصال فقط، بلا فهرسة)."""

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.errors import AppError, ErrorCode
from app.db.models import Base


def get_engine(database_url: str) -> Engine:
    """رابط DB ← محرك مشترك. لا يتصل فعليا حتى أول استعلام."""
    return create_engine(database_url, pool_pre_ping=True)


def create_tables(engine: Engine) -> None:
    """ينشئ كل جداول العمل للاختبار والسكربتات فقط (sqlite في الذاكرة).

    ممنوع استدعاؤها عند إقلاع API — الإقلاع يستخدم Alembic عبر app.db.migrate.
    """
    import app.auth.models as _auth_models  # noqa: F401 - تسجيل users قبل create_all
    import app.db.models as _models  # noqa: F401 - تسجيل knowledge_chunks

    Base.metadata.create_all(engine)


def check_connection(engine: Engine) -> None:
    """يفحص الاتصال بأمر خفيف. ينجح بصمت أو يرمي خطأ عربيا صريحا."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise AppError(
            ErrorCode.DB_CONNECTION_FAILED,
            "تعذر الاتصال بقاعدة البيانات. تحقق من DATABASE_URL وأن Postgres يعمل.",
            status=503,
        ) from exc


def dispose_engine(engine: Engine) -> None:
    """يغلق مقابس المحرك عند إيقاف التطبيق."""
    engine.dispose()
