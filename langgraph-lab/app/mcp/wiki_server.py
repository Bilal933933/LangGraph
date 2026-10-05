"""خادم MCP لويكيبيديا (بحث + مقال، مجاني بلا مفتاح)."""

from fastmcp import FastMCP

mcp = FastMCP("wiki-server")

_API = "https://ar.wikipedia.org/w/api.php"


@mcp.tool
def search_wikipedia(query: str, limit: int = 5) -> str:
    """يبحث في ويكيبيديا العربية عن عناوين مرتبطة."""
    import httpx

    cleaned = query.strip()[:200]
    if not cleaned:
        return "اكتب استعلامًا غير فارغ."
    safe = max(1, min(int(limit), 10))
    try:
        res = httpx.get(
            _API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": cleaned,
                "srlimit": safe,
                "format": "json",
            },
            timeout=15.0,
        )
        if res.status_code != 200:
            return "تعذر البحث الآن."
        hits = res.json().get("query", {}).get("search", [])
    except Exception:
        return "تعذر البحث الآن."
    if not hits:
        return "لا نتائج في ويكيبيديا."
    return "النتائج:\n" + "\n".join(f"- {h.get('title', '')}" for h in hits[:safe])


@mcp.tool
def fetch_article(title: str, max_chars: int = 6000) -> str:
    """يجلب نص مقال ويكيبيديا بعنوانه الدقيق."""
    import httpx

    cleaned = title.strip()[:200]
    if not cleaned:
        return "اكتب عنوان مقال غير فارغ."
    try:
        res = httpx.get(
            _API,
            params={
                "action": "query",
                "prop": "extracts",
                "explaintext": True,
                "titles": cleaned,
                "format": "json",
            },
            timeout=15.0,
        )
        if res.status_code != 200:
            return "تعذر الجلب الآن."
        pages = res.json().get("query", {}).get("pages", {})
    except Exception:
        return "تعذر الجلب الآن."
    for page in pages.values():
        text = str(page.get("extract") or "").strip()
        if text and "missing" not in page:
            safe = max(500, min(int(max_chars), 20000))
            return text[:safe]
    return "المقال غير موجود."


if __name__ == "__main__":
    mcp.run()
