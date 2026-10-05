"""أداة القراءة الدقيقة (معرف المقطع ← النص الكامل)."""

from langchain_core.tools import BaseTool, tool

from app.domain.ports import KnowledgeSourcePort


def make_fetch_source_tool(repo: KnowledgeSourcePort) -> BaseTool:
    """مصنع القراءة الدقيقة: معرف من نتائج search ← النص الكامل.

    بلا معرف صالح ← رسالة إرشاد لا خطأ خام (يُبقي حلقة الوكيل مستقرة).
    """

    @tool
    def fetch_source(chunk_id: int) -> str:
        """يقرأ النص الكامل لمقطع ظهر في نتائج البحث بمعرفه."""
        try:
            cid = int(chunk_id)
        except Exception:
            return "معرف المقطع يجب أن يكون رقمًا صحيحًا موجبًا من نتائج البحث."
        if cid <= 0:
            return "معرف المقطع يجب أن يكون رقمًا صحيحًا موجبًا من نتائج البحث."
        try:
            row = repo.get_source(cid)
        except Exception:
            return "تعذر قراءة المقطع الآن، أجب من المقتطفات المتاحة."
        if row is None:
            return f"لا يوجد مقطع بالمعرف {cid} في مصادر هذه الجلسة."
        title = str(row.get("title") or "").strip()
        lesson = str(row.get("lesson") or "").strip()
        text = str(row.get("text") or "").strip()
        head = " / ".join(p for p in (title, lesson) if p) or f"مقطع {cid}"
        return f"[{head}]: {text[:4000]}"

    return fetch_source
