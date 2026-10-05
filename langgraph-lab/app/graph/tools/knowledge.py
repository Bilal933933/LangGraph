"""أداة البحث المعرفي (استكشاف داخل حلقة الوكيل)."""

from langchain_core.tools import BaseTool, tool

from app.domain.ports import KnowledgeSearchPort


def make_search_knowledge_tool(
    repo: KnowledgeSearchPort, limit: int = 5
) -> BaseTool:
    """مصنع البحث: سؤال ← مقاطع `{id,title,lesson}` بلا نصوص كاملة.

    النص الكامل عبر `fetch_source` لاحقًا بالمعرف (مرحلتان).
    """

    @tool
    def search_knowledge(query: str) -> str:
        """يبحث في منهجنا عن مقاطع مرتبطة بالسؤال."""
        cleaned = query.strip()[:500]
        if not cleaned:
            return "اكتب سؤالًا غير فارغ للبحث في المنهج."
        try:
            hybrid = getattr(repo, "search_hybrid", None)
            if callable(hybrid):
                chunks = hybrid(cleaned, limit)
            else:
                chunks = repo.search(cleaned, limit)
        except Exception:
            return "تعذر البحث الآن، أجب من معرفتك العامة."
        if not chunks:
            return "لا توجد مقاطع مرتبطة في المنهج."
        lines: list[str] = []
        for c in chunks[: max(1, limit)]:
            cid = c.get("id", "?")
            title = str(c.get("title") or "").strip()
            lesson = str(c.get("lesson") or "").strip()
            label = " / ".join(p for p in (title, lesson) if p) or "مقطع"
            lines.append(f"- [{cid}] {label}")
        return "المقاطع المرتبطة:\n" + "\n".join(lines)

    return search_knowledge
