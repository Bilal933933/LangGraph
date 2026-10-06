"""خادم MCP لجلب الصفحات (رابط معلوم ← نص، مجاني بلا مفتاح)."""

from fastmcp import FastMCP

from app.mcp.fetch_guard import fetch_text

mcp = FastMCP("fetch-server")


@mcp.tool
def fetch_url(url: str, max_chars: int = 6000) -> str:
    """يجلب نص صفحة ويب برابطها المباشر (مضيف عام فقط، بلا شبكات داخلية)."""
    return fetch_text(url, max_chars)


if __name__ == "__main__":
    mcp.run()
