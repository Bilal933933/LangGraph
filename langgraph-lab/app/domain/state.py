"""الحالة (State = الذاكرة المشتركة بين العقد)."""

from typing import Annotated, NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.domain.models import Intent, LessonPlan, LessonRequest, QuizRequest


def _append_sections(
    left: list[dict[str, object]], right: list[dict[str, object]] | dict[str, object]
) -> list[dict[str, object]]:
    """مخفض التجميع للعمال المتوازيين: قوائم ← دمج بلا فقد."""
    if isinstance(right, dict):
        return [*left, right]
    return [*left, *right]


PLAN_SECTION_KINDS: tuple[str, ...] = ("objectives", "intro", "steps", "activities", "assessment")


class ChatState(TypedDict):
    """حالة مولد الاختبارات: رسائل + هوية + نية + طلب + نواقص.

    add_messages = مخفّض (Reducer) يدمج الرسائل الجديدة مع القديمة
    بدل استبدالها.

    قاعدة الهوية مقابل السياق: الحالة تحمل الهوية فقط (teacher_id)
    للعقد التي تحتاجها، أما التفاصيل (اسم، بريد، تفضيلات) فتجلبها
    العقدة المحتاجة من المستودع عند الوصول إليها، ولا تخزن في
    اللقطة (Checkpoint) لتجنب نسخة ثانية من قاعدة البيانات.
    أي حقل جديد يضاف كـ NotRequired فقط عند ظهور ميزة تحتاجه.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    teacher_id: NotRequired[int | None]
    intent: NotRequired[Intent]
    quiz_request: NotRequired[QuizRequest]
    missing_fields: NotRequired[list[str]]
    pending_profile_name: NotRequired[str | None]
    profile_snapshot: NotRequired[dict[str, object]]
    pending_profile: NotRequired[dict[str, object] | None]
    retrieved_sources: NotRequired[list[dict[str, object]]]
    lesson_request: NotRequired[LessonRequest]
    section_task: NotRequired[str | None]
    plan_sections: NotRequired[Annotated[list[dict[str, object]], _append_sections]]
    plan_draft: NotRequired[LessonPlan]
