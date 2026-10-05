"""مستودع الملفات المحلية (مجلد data فقط، حتمي بلا LLM)."""

from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent.parent / "data"


def _safe(name: str) -> Path | None:
    """اسم نسبي ← مسار داخل data، وغيره ← None."""
    cleaned = name.strip().replace("\\", "/").lstrip("/")
    if not cleaned or ".." in cleaned.split("/"):
        return None
    target = (_BASE / cleaned).resolve()
    try:
        target.relative_to(_BASE.resolve())
    except ValueError:
        return None
    return target


class LocalFilesRepository:
    """سرد وقراءة نصية بحدود (2MB / 20k حرف)."""

    def list(self, subdir: str = "") -> list[str]:
        """مجلد فرعي ← أسماء مرتبة أو [] عند الغياب."""
        base = _safe(subdir) if subdir.strip() else _BASE.resolve()
        if base is None or not base.is_dir():
            return []
        return sorted(p.name for p in base.iterdir())

    def read(self, name: str, max_chars: int = 6000) -> str | None:
        """اسم ملف ← نصه أو None (مفقود/كبير/غير نصي)."""
        target = _safe(name)
        if target is None or not target.is_file():
            return None
        if target.stat().st_size > 2 * 1024 * 1024:
            return None
        try:
            text = target.read_text(encoding="utf-8", errors="replace").strip()
        except Exception:
            return None
        if not text:
            return None
        return text[: max(500, min(int(max_chars), 20000))]
