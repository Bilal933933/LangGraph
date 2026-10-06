"""موجه استيضاح ورقة العمل (نواقص ← سؤال، والمكتمل ← استرجاع)."""

from typing import Literal

from app.domain.state import ChatState
from app.graph.edges.plan.shared import has_missing

WorksheetExtractTarget = Literal["worksheet_ask", "worksheet_retrieve"]


def route_after_worksheet_extract(state: ChatState) -> WorksheetExtractTarget:
    """نواقص ورقة العمل ← سؤال، والمكتمل ← استرجاع المصادر."""
    if has_missing(state):
        return "worksheet_ask"
    return "worksheet_retrieve"
