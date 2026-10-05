"""موجه استيضاح الاختبار (نواقص ← سؤال، والمكتمل ← تأكيد)."""

from typing import Literal

from app.domain.state import ChatState
from app.graph.edges.plan.shared import has_missing

ExtractTarget = Literal["ask_clarification", "confirm_ready"]


def route_after_extract(state: ChatState) -> ExtractTarget:
    """الحقول الناقصة ← استيضاح أو تأكيد الاكتمال."""
    if has_missing(state):
        return "ask_clarification"
    return "confirm_ready"
