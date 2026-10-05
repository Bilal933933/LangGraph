"""محول بحث الويب (قدرة معزولة عن Core)."""

from typing import Any


class StubWebSearch:
    """بديل آمن: أي استعلام ← قائمة فارغة."""

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """نص السؤال ← [] دائمًا (لا شبكة في الاختبارات)."""
        _ = (query, limit)
        return []


class TavilyWebSearch:
    """بحث Tavily عبر httpx (بلا اعتماد جديد): مفتاح ← نتائج موحدة."""

    def __init__(self, api_key: str, timeout: float = 10.0) -> None:
        self._key = api_key
        self._timeout = timeout

    def search(self, query: str, limit: int = 5) -> list[dict[str, object]]:
        """استعلام ← [{title, text, url}] أو [] عند أي فشل."""
        import httpx

        cleaned = query.strip()[:500]
        if not cleaned or not self._key.strip():
            return []
        safe = max(1, min(int(limit), 10))
        try:
            res = httpx.post(
                "https://api.tavily.com/search",
                json={"api_key": self._key, "query": cleaned, "max_results": safe},
                timeout=self._timeout,
            )
            if res.status_code != 200:
                return []
            items = res.json().get("results", [])
        except Exception:
            return []
        out: list[dict[str, object]] = []
        for it in items[:safe]:
            if not isinstance(it, dict):
                continue
            text = str(it.get("content") or "").strip()
            if not text:
                continue
            out.append(
                {
                    "title": str(it.get("title") or "").strip(),
                    "text": text[:1500],
                    "url": str(it.get("url") or "").strip(),
                }
            )
        return out


def build_web_search(settings: Any) -> StubWebSearch | TavilyWebSearch:
    """مفتاح موجود ← Tavily حقيقي، غائب ← Stub آمن."""
    key = settings.tavily_api_key.get_secret_value().strip()
    if not key:
        return StubWebSearch()
    return TavilyWebSearch(key, settings.web_timeout_seconds)
