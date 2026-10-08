"""مصنع الحافظ (Checkpointer = ذاكرة اللقطات بين الطلبات).

الفصل: جداول التطبيق (Teacher/Conversation/Message) ننشئها نحن عبر
SQLAlchemy، وجداول اللقطات (checkpoints/checkpoint_writes/checkpoint_blobs)
ينشئها LangGraph عبر `PostgresSaver.setup()` ولا نلمسها يدويًا.

قاعدة الإصدارات الحديثة: مسارات الرسم عندنا غير متزامنة دائما
(`ainvoke/astream`)، لذلك حافظ Postgres يجب أن يكون `AsyncPostgresSaver`
الذي يملك `aget_tuple/aput`. النسخة المتزامنة `PostgresSaver` ترفع
`NotImplementedError` داخل `AsyncPregelLoop` وتكسر كل الرسائل.
"""

from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager
from functools import lru_cache

from langgraph.checkpoint.memory import InMemorySaver


def normalize_postgres_url(database_url: str) -> str:
    """يحول رابط SQLAlchemy إلى صيغة psycopg للـ Checkpointer."""
    cleaned = database_url.strip()
    return cleaned.replace("postgresql+psycopg://", "postgresql://", 1)


@lru_cache(maxsize=1)
def create_checkpointer() -> InMemorySaver:
    """حافظ التطوير/الاختبار: ذاكرة فقط، تُفقد عند إعادة التشغيل."""
    return InMemorySaver()


@contextmanager
def postgres_checkpointer_cm(database_url: str) -> Iterator[object]:
    """سياق PostgresSaver المتزامن (legacy: لا يصلح لمسارات ainvoke/astream).

    أبقيناه للتوافق الخلفي فقط. كود التطبيق يستخدم
    `async_postgres_checkpointer_cm` أدناه.
    """
    from langgraph.checkpoint.postgres import PostgresSaver

    normalized = normalize_postgres_url(database_url)
    with PostgresSaver.from_conn_string(normalized) as checkpointer:
        yield checkpointer


@asynccontextmanager
async def async_postgres_checkpointer_cm(database_url: str) -> AsyncIterator[object]:
    """سياق AsyncPostgresSaver حي: اتصال واحد لعمر العملية لمسارات async."""
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    normalized = normalize_postgres_url(database_url)
    async with AsyncPostgresSaver.from_conn_string(normalized) as checkpointer:
        yield checkpointer


def setup_postgres_tables(database_url: str) -> None:
    """ينشئ جداول اللقطات أول مرة فقط. آمن للتكرار (idempotent)."""
    from langgraph.checkpoint.postgres import PostgresSaver

    from app.core.errors import AppError, ErrorCode

    normalized = normalize_postgres_url(database_url)
    try:
        with PostgresSaver.from_conn_string(normalized) as checkpointer:
            checkpointer.setup()
    except Exception as exc:
        raise AppError(
            ErrorCode.DB_CONNECTION_FAILED,
            "تعذر تهيئة جداول LangGraph. تحقق من DATABASE_URL وأن Postgres يعمل.",
            status=503,
        ) from exc
