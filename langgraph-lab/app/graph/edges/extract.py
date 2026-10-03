"""موجه الاستخراج (extract ← استيضاح أو تأكيد)."""

from typing import Literal

from app.domain.state import ChatState

ExtractTarget = Literal["ask_clarification", "confirm_ready"]


def route_after_extract(state: ChatState) -> ExtractTarget:
    """الحقول الناقصة ← استيضاح أو تأكيد الاكتمال."""
    if state.get("missing_fields"):
        return "ask_clarification"
    return "confirm_ready"
