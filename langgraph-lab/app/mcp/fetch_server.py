"""خادم MCP لجلب الصفحات (رابط معلوم ← نص، مجاني بلا مفتاح)."""

from fastmcp import FastMCP

mcp = FastMCP("fetch-server")


@mcp.tool
def fetch_url(url: str, max_chars: int = 6000) -> str:
    """يجلب نص صفحة ويب برابطها المباشر."""
    import httpx

    cleaned = url.strip()[:2000]
    if not (cleaned.startswith("http://") or cleaned.startswith("https://")):
        return "الرابط يجب أن يبدأ بـ http:// أو https://."
    try:
        res = httpx.get(cleaned, timeout=15.0, follow_redirects=True)
        if res.status_code != 200:
            return f"تعذر الجلب (HTTP {res.status_code})."
        text = res.text.strip()
    except Exception:
        return "تعذر الجلب الآن."
    if not text:
        return "الصفحة فارغة."
    safe = max(500, min(int(max_chars), 20000))
    return text[:safe]


if __name__ == "__main__":
    mcp.run()
