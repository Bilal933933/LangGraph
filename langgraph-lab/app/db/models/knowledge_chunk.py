"""جدول مقاطع المعرفة (نسخة مطابقة للمصدر ai-grammar-tutor لاستقبال النسخ الكامل)."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import ARRAY, JSON, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base

# توافق الاختبارات: بوستجرس يستخدم الأنواع الأصلية، sqlite يسقط لبدائل بسيطة.
_CONCEPTS_TYPE = ARRAY(String).with_variant(JSON(), "sqlite")
_EMBEDDING_TYPE = Vector(384).with_variant(JSON(), "sqlite")
_SEARCH_VECTOR_TYPE = TSVECTOR().with_variant(Text(), "sqlite")


class KnowledgeChunk(Base):
    """قطعة معرفة: نص + تضمين 384 + بحث نصي. البعد ثابت لمطابقة e5-small."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    doc_key: Mapped[str | None] = mapped_column(String(64), unique=True, index=True, default=None)
    doc_path: Mapped[str | None] = mapped_column(String(512), default=None)
    doc_type: Mapped[str | None] = mapped_column(String(32), default="general")

    grade: Mapped[str | None] = mapped_column(String(32), index=True, default=None)
    stage: Mapped[str | None] = mapped_column(String(32), index=True, default=None)
    subject: Mapped[str | None] = mapped_column(String(128), index=True, default=None)
    branch: Mapped[str | None] = mapped_column(String(128), index=True, default=None)
    source_type: Mapped[str | None] = mapped_column(String(32), index=True, default=None)
    book_id: Mapped[str | None] = mapped_column(String(128), index=True, default=None)
    unit: Mapped[str | None] = mapped_column(String(255), default=None)
    lesson: Mapped[str | None] = mapped_column(String(255), default=None)
    term: Mapped[str | None] = mapped_column(String(32), index=True, default=None)
    parent_section: Mapped[str | None] = mapped_column(String(512), index=True, default=None)
    chunk_index: Mapped[int | None] = mapped_column(Integer, default=None)
    chunk_token_count: Mapped[int | None] = mapped_column(Integer, default=None)
    concepts: Mapped[list[str] | None] = mapped_column(_CONCEPTS_TYPE, default=None)

    title: Mapped[str | None] = mapped_column(String(255), default=None)
    text: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[str | None] = mapped_column(String(255), default=None)
    page: Mapped[int | None] = mapped_column(Integer, default=None)
    embedding: Mapped[list[float] | None] = mapped_column(_EMBEDDING_TYPE, default=None)
    search_text: Mapped[str | None] = mapped_column(Text, default=None)
    search_vector = mapped_column(_SEARCH_VECTOR_TYPE, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), default=None
    )

    __table_args__ = (
        Index("ix_knowledge_chunks_grade_subject", "grade", "subject"),
        Index("ix_knowledge_chunks_stage_subject", "stage", "subject"),
        Index("ix_knowledge_chunks_source_type_subject", "source_type", "subject"),
        Index(
            "ix_knowledge_chunks_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
        ),
        Index("ix_chunks_term", "term"),
        Index("ix_chunks_parent", "parent_section"),
        Index("ix_chunks_book_lesson", "book_id", "lesson"),
    )
