"""مستودع المعرفة من Postgres (هجين: دلالي HNSW + نصي GIN، باحتياط نصي)."""

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.engine import get_engine

_AR_WORD = re.compile(r"[\u0600-\u06FF]{3,}")


def _keywords_fallback(query: str) -> str | None:
    """كلمات عربية طولها 3+ (تتجاهل ما/هو/...) ← `أ | ب` أو None."""
    seen: list[str] = []
    for word in _AR_WORD.findall(query):
        if word not in seen:
            seen.append(word)
        if len(seen) >= 6:
            break
    if not seen:
        return None
    return " | ".join(seen)


class PgKnowledgeRepository:
    """بحث `search_vector @@ plainto_tsquery` بجلسات قصيرة مثل SqlTeacher."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def search_hybrid(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← دمج دلالي (HNSW) + نصي (GIN). فشل التضمين ← نصي فقط."""
        safe = max(1, min(int(limit), 50))
        pool = min(max(safe * 3, 15), 50)
        family_cap = max(2, safe // 6)
        try:
            from app.knowledge.embeddings import embed_query

            vector = embed_query(query)
        except Exception:
            return self.search(query, safe)
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                sem = session.execute(
                    text(
                        "SELECT title, text, subject, lesson "
                        "FROM knowledge_chunks "
                        "ORDER BY embedding <=> CAST(:v AS vector) "
                        "LIMIT :lim"
                    ),
                    {
                        "v": "[" + ",".join(f"{x:.6f}" for x in vector) + "]",
                        "lim": pool,
                    },
                ).all()
                lex = [
                    (c["title"], c["text"], c["subject"], c["lesson"])
                    for c in self.search(query, pool)
                ]
                def _family(title: str) -> str:
                    """عائلة الكتاب: ما قبل أول فاصل (جزء/شرطة/قوس)."""
                    cut = len(title)
                    for sep in ("—", "-", "(", "جزء", "الجزء"):
                        i = title.find(sep)
                        if i > 0:
                            cut = min(cut, i)
                    return title[:cut].strip() or title.strip()

                merged: list[tuple[object, object, object, object]] = []
                seen: set[tuple[object, object]] = set()
                family_count: dict[str, int] = {}
                for pair in zip(sem, lex, strict=False):
                    for row in pair:
                        key = (row[0], row[1])
                        family = _family(str(row[0] or ""))
                        if key in seen or family_count.get(family, 0) >= family_cap:
                            continue
                        merged.append(row)
                        seen.add(key)
                        family_count[family] = family_count.get(family, 0) + 1
                for row in (*sem, *lex):
                    key = (row[0], row[1])
                    family = _family(str(row[0] or ""))
                    if key in seen or family_count.get(family, 0) >= family_cap:
                        continue
                    merged.append(row)
                    seen.add(key)
                    family_count[family] = family_count.get(family, 0) + 1
                return [
                    {
                        "title": str(r[0] or "").strip(),
                        "text": str(r[1] or "").strip()[:1500],
                        "subject": str(r[2] or "").strip(),
                        "lesson": str(r[3] or "").strip(),
                    }
                    for r in merged[:safe]
                    if str(r[1] or "").strip()
                ]
        finally:
            engine.dispose()

    def get_source(self, chunk_id: int) -> dict[str, object] | None:
        """معرف المقطع ← {id, title, text, subject, lesson} أو None.

        حارس: غير موجب ← None بلا استعلام (يمنع حقن المسارات).
        """
        if not isinstance(chunk_id, int) or chunk_id <= 0:
            return None
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                row = session.execute(
                    text(
                        "SELECT id, title, text, subject, lesson "
                        "FROM knowledge_chunks WHERE id = :i LIMIT 1"
                    ),
                    {"i": chunk_id},
                ).first()
                if row is None or not str(row[2] or "").strip():
                    return None
                return {
                    "id": int(row[0]),
                    "title": str(row[1] or "").strip(),
                    "text": str(row[2] or "").strip()[:4000],
                    "subject": str(row[3] or "").strip(),
                    "lesson": str(row[4] or "").strip(),
                }
        finally:
            engine.dispose()

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← مقاطع {title, text, subject, lesson} الأعلى صلة."""
        cleaned = query.strip()
        if not cleaned:
            return []
        safe = max(1, min(int(limit), 50))
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                rows = session.execute(
                    text(
                        "SELECT title, text, subject, lesson "
                        "FROM knowledge_chunks "
                        "WHERE search_vector @@ plainto_tsquery('simple', :q) "
                        "ORDER BY ts_rank(search_vector, plainto_tsquery('simple', :q)) DESC "
                        "LIMIT :lim"
                    ),
                    {"q": cleaned[:500], "lim": safe},
                ).all()
                if not rows:
                    fallback = _keywords_fallback(cleaned)
                    if fallback is not None:
                        rows = session.execute(
                            text(
                                "SELECT title, text, subject, lesson "
                                "FROM knowledge_chunks "
                                "WHERE search_vector @@ to_tsquery('simple', :q) "
                                "ORDER BY ts_rank(search_vector, to_tsquery('simple', :q)) DESC "
                                "LIMIT :lim"
                            ),
                            {"q": fallback, "lim": safe},
                        ).all()
                return [
                    {
                        "title": (r[0] or "").strip(),
                        "text": (r[1] or "").strip()[:1500],
                        "subject": (r[2] or "").strip(),
                        "lesson": (r[3] or "").strip(),
                    }
                    for r in rows
                    if (r[1] or "").strip()
                ]
        finally:
            engine.dispose()
