"""موجه استيضاح خطة التحضير (نواقص ← سؤال، والمكتمل ← استرجاع)."""

from typing import Literal

from app.domain.state import ChatState
from app.graph.edges.plan.shared import has_missing

PlanExtractTarget = Literal["plan_ask", "plan_retrieve"]


def route_after_plan_extract(state: ChatState) -> PlanExtractTarget:
    """نواقص التحضير ← سؤال، والمكتمل ← استرجاع المصادر."""
    if has_missing(state):
        return "plan_ask"
    return "plan_retrieve"
