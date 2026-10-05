"""فهرسة المعرفة: إضافات المتجهات + فهرس HNSW الدلالي. بوستجرس فقط."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def ensure_vector_extensions(engine: Engine) -> None:
    """يثبت إضافتي vector وpg_trgm إن توفرتا. آمن للتكرار. بوستجرس فقط."""
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))


def ensure_knowledge_indexes(engine: Engine) -> None:
    """ينشئ فهرس HNSW الدلالي إن غاب. بوستجرس فقط، آمن للتكرار."""
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw "
                "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
            )
        )


def setup_knowledge_db(engine: Engine) -> None:
    """يجهز DB المعرفة بالترتيب: إضافات ← جداول (عبر create_tables) ← فهارس."""
    from app.db.engine import create_tables

    ensure_vector_extensions(engine)
    create_tables(engine)
    ensure_knowledge_indexes(engine)
