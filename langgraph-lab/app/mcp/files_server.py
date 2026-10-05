"""خادم MCP للملفات المحلية (مجلد data فقط، بلا مفتاح)."""

from pathlib import Path

from fastmcp import FastMCP

mcp = FastMCP("files-server")

_BASE = Path(__file__).resolve().parent.parent.parent / "data"


def _safe_path(name: str) -> Path | None:
    """اسم ملف ← مسار داخل data فقط، وغيره ← None (منع traversal)."""
    cleaned = name.strip().replace("\\", "/").lstrip("/")
    if not cleaned or ".." in cleaned.split("/") or cleaned.startswith("/"):
        return None
    target = (_BASE / cleaned).resolve()
    try:
        target.relative_to(_BASE.resolve())
    except ValueError:
        return None
    return target


@mcp.tool
def list_data_dir(subdir: str = "") -> str:
    """يسرد ملفات مجلد data (أو مجلد فرعي منه)."""
    base = _safe_path(subdir) if subdir.strip() else _BASE.resolve()
    if base is None or not base.is_dir():
        return "المجلد غير موجود داخل data."
    names = sorted(p.name for p in base.iterdir())
    return "الملفات:\n" + "\n".join(f"- {n}" for n in names) if names else "المجلد فارغ."


@mcp.tool
def read_data_file(name: str, max_chars: int = 6000) -> str:
    """يقرأ ملفًا نصيًا داخل data باسمه النسبي."""
    target = _safe_path(name)
    if target is None or not target.is_file():
        return "الملف غير موجود داخل data."
    if target.stat().st_size > 2 * 1024 * 1024:
        return "الملف كبير (أكثر من 2MB)."
    try:
        text = target.read_text(encoding="utf-8", errors="replace").strip()
    except Exception:
        return "تعذر قراءة الملف."
    safe = max(500, min(int(max_chars), 20000))
    return text[:safe] if text else "الملف فارغ."


if __name__ == "__main__":
    mcp.run()
