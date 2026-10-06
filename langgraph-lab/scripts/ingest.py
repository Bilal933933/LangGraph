"""الاستيعاب: ملفات data/*.md ← مقاطع ← تضمين e5 ← upsert في knowledge_chunks.

الاستخدام (من جذر langgraph-lab):
    uv run python scripts/ingest.py --dry-run
    uv run python scripts/ingest.py

المعرف المستقر doc_key = بصمة المسار النسبي: إعادة التشغيل تستبدل
مقاطع المستند نفسه بدل التكرار. التفاصيل في data/SOURCES.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import get_settings  # noqa: E402
from app.db.engine import get_engine  # noqa: E402
from app.db.knowledge_indexes import (  # noqa: E402
    ensure_knowledge_indexes,
    ensure_vector_extensions,
)
from app.db.models.knowledge_chunk import KnowledgeChunk  # noqa: E402
from app.knowledge.chunking import doc_key_for, split_markdown  # noqa: E402
from app.knowledge.embeddings import embed_passage  # noqa: E402
from app.knowledge.metadata import derive_metadata  # noqa: E402


def _iter_docs(data_dir: Path, only: list[str]) -> list[Path]:
    """مجلد البيانات ← ملفات .md مرتبة (تصفية اختيارية ببادئة مسار)."""
    docs = sorted(data_dir.rglob("*.md"))
    if only:
        docs = [d for d in docs if any(str(_rel(data_dir, d)).startswith(o) for o in only)]
    return docs


def _rel(data_dir: Path, doc: Path) -> str:
    """مسار مطلق ← نسبي posix ثابت عبر الأنظمة."""
    return doc.relative_to(data_dir).as_posix()


def ingest_doc(session: Session, data_dir: Path, doc: Path, max_chars: int, overlap: int) -> int:
    """مستند واحد ← حذف مقاطعه القديمة ← إدخال الجديدة. يعيد عدد المقاطع."""
    rel = _rel(data_dir, doc)
    key = doc_key_for(rel)
    text = doc.read_text(encoding="utf-8")
    chunks = split_markdown(text, max_chars=max_chars, overlap_words=overlap)
    session.query(KnowledgeChunk).filter(KnowledgeChunk.doc_key == key).delete()
    meta = derive_metadata(rel, chunks[0].title if chunks else "")
    for i, chunk in enumerate(chunks):
        lesson = chunk.title or meta["lesson"]
        title = lesson or doc.stem
        session.add(
            KnowledgeChunk(
                doc_key=key,
                doc_path=rel,
                doc_type="textbook" if rel.startswith("textbook/") else "reference",
                grade=meta["grade"],
                stage=meta["stage"],
                subject=meta["subject"],
                book_id=meta["book_id"],
                lesson=lesson,
                chunk_index=i,
                chunk_token_count=chunk.token_count,
                title=title,
                text=chunk.text,
                source=rel,
                embedding=embed_passage(chunk.text),
                search_text=chunk.text,
                search_vector=func.to_tsvector("simple", chunk.text),
            )
        )
    return len(chunks)


def main(argv: list[str] | None = None) -> int:
    """يحلل الوسائط ← يستوعب ← يطبع الإحصاء. 0 نجاح."""
    parser = argparse.ArgumentParser(description="استيعاب data/ إلى knowledge_chunks")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--only", action="append", default=[], help="بادئة مسار نسبي (تتكرر)")
    parser.add_argument("--limit-docs", type=int, default=0, help="سقف المستندات (0 = الكل)")
    parser.add_argument("--max-chars", type=int, default=2000)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--dry-run", action="store_true", help="تقطيع فقط بلا DB")
    args = parser.parse_args(argv)

    data_dir = (ROOT / args.data_dir).resolve()
    docs = _iter_docs(data_dir, args.only)
    if args.limit_docs > 0:
        docs = docs[: args.limit_docs]
    if args.dry_run:
        total = sum(len(split_markdown(d.read_text(encoding="utf-8"))) for d in docs)
        print(f"dry-run: docs={len(docs)} chunks={total}")
        return 0

    database_url = get_settings().database_url.get_secret_value().strip()
    if not database_url:
        print("DATABASE_URL فارغ في .env", file=sys.stderr)
        return 2
    engine = get_engine(database_url)
    if engine.dialect.name != "postgresql":
        print("الاستيعاب يستهدف Postgres فقط (pgvector).", file=sys.stderr)
        return 2
    ensure_vector_extensions(engine)
    total_chunks = 0
    try:
        with Session(engine) as session:
            for doc in docs:
                count = ingest_doc(session, data_dir, doc, args.max_chars, args.overlap)
                total_chunks += count
                print(f"+ {_rel(data_dir, doc)}: {count}")
            session.commit()
        ensure_knowledge_indexes(engine)
    finally:
        engine.dispose()
    print(f"done: docs={len(docs)} chunks={total_chunks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
