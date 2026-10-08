"""الحالة (State = الذاكرة المشتركة بين العقد)."""

from typing import Annotated, NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.domain.models import (
    CanonicalRequest,
    Intent,
    LessonPlan,
    LessonRequest,
    QuizRequest,
    TeacherContext,
    WorksheetRequest,
)
from app.domain.outputs.quiz import QuizOutput
from app.domain.outputs.worksheet import WorksheetOutput


def _append_sections(
    left: list[dict[str, object]], right: list[dict[str, object]] | dict[str, object]
) -> list[dict[str, object]]:
    """مخفض التجميع للعمال المتوازيين: قوائم ← دمج بلا فقد.

    قاعدة التصفير: قائمة فارغة تعني بداية طلب جديد ← تُهمل القديمة.
    بلا هذا يتسرب قسم خطة سابقة إلى خطة لاحقة في نفس thread.
    """
    if isinstance(right, dict):
        return [*left, right]
    if not right:
        return []
    return [*left, *right]


PLAN_SECTION_KINDS: tuple[str, ...] = ("objectives", "intro", "steps", "activities", "assessment")


class ChatState(TypedDict):
    """حالة الرسم: رسائل + سياق + طلب موحد + تنفيذ.

    add_messages = مخفّض (Reducer) يدمج الرسائل الجديدة مع القديمة
    بدل استبدالها.

    الفصل المعتمد: Message (ماذا قال؟) ≠ Request (ماذا فهمنا؟)
    ≠ State (أين وصل التنفيذ؟) ≠ Checkpoint (حفظ التنفيذ)
    ≠ Context (ماذا يحتاج النموذج ضمن ميزانية التوكن؟).

    قاعدة الهوية مقابل الفهم: teacher_id وruntime_context من
    Authentication (المصادقة) وDB فقط، لا يستنتجهما LLM.
    أي حقل جديد يضاف كـ NotRequired فقط عند ظهور ميزة تحتاجه.

    الشكل المستهدف:
    - messages: سجل التنفيذ الحي.
    - runtime_context: سياق المعلم المحمل حتميا.
    - canonical_request: الطلب الفعلي الحالي للتوجيه.
    - execution: retrieved_sources + plan_sections + plan_draft.
    - response: آخر AIMessage في messages (لا حقل منفصل).

    ملكية الحقول (Phase 2 + Canonical):
    - حقن Runtime كل دور: teacher_id (لا اعتماد على Checkpoint له).
    - سياق محمل حتميا: runtime_context.
    - طلب موحد صغير للتوجيه: canonical_request (يكبر عبر Revision
      بـ parent_request_id، لا بإعادة إنشاء دائما).
    - قرار Graph مؤقت (legacy حتى الهجرة): intent.
    - تراكم متعدد الأدوار (legacy حتى الهجرة): quiz_request,
      worksheet_request, lesson_request, missing_fields.
    - مؤقت يُصفّر بعد الاستخدام: pending_profile, pending_profile_name.
    - ناتج الدور: retrieved_sources.
    - Send فقط: section_task (يُصفّر في plan_merge).
    - تجميع متوازي: plan_sections (يُصفّر في plan_extract الجديد).
    - ناتج نهائي: plan_draft.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    teacher_id: NotRequired[int | None]
    runtime_context: NotRequired[TeacherContext]
    canonical_request: NotRequired[CanonicalRequest]
    intent: NotRequired[Intent]
    quiz_request: NotRequired[QuizRequest]
    worksheet_request: NotRequired[WorksheetRequest]
    missing_fields: NotRequired[list[str]]
    pending_profile_name: NotRequired[str | None]
    profile_snapshot: NotRequired[dict[str, object]]
    pending_profile: NotRequired[dict[str, object] | None]
    retrieved_sources: NotRequired[list[dict[str, object]]]
    lesson_request: NotRequired[LessonRequest]
    section_task: NotRequired[str | None]
    plan_sections: NotRequired[Annotated[list[dict[str, object]], _append_sections]]
    plan_draft: NotRequired[LessonPlan]
    quiz_draft: NotRequired[QuizOutput]
    worksheet_draft: NotRequired[WorksheetOutput]
