"""المساعد المشترك لموجهات الاستيضاح (فحص النواقص فقط)."""

from app.domain.state import ChatState


def has_missing(state: ChatState) -> bool:
    """الحالة ← True عند وجود حقول ناقصة."""
    return bool(state.get("missing_fields"))
