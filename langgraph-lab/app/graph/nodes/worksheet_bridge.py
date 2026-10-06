"""جسر ورقة العمل من الخطة (منطق فقط، لا برومبتات هنا)."""

from app.domain.models import LessonPlan, WorksheetRequest
from app.graph.prompts.runtime.worksheet import WORKSHEET_SHAPE_SYSTEM


def build_worksheet_shape_prompt(request: WorksheetRequest | None) -> str:
    """طلب ← نص شكل ملزم يدمج في prompt عقدة الكتابة."""
    kind = request.kind if request and request.kind else "worksheet"
    topic = request.topic if request and request.topic else "غير محدد"
    grade = request.grade_level if request and request.grade_level else "غير محدد"
    if kind == "activity":
        minutes = request.minutes if request and request.minutes else 15
        spec = f"النوع: نشاط صفي — الموضوع: {topic} — الصف: {grade} — الزمن: {minutes} دقيقة"
    else:
        num = request.num_items if request and request.num_items else 8
        spec = f"النوع: ورقة عمل — الموضوع: {topic} — الصف: {grade} — العدد: {num}"
    return f"{WORKSHEET_SHAPE_SYSTEM}\n{spec}"


def worksheet_request_from_plan(plan: LessonPlan) -> WorksheetRequest:
    """خطة درس ← طلب ورقة عمل جاهز لزر (ورقة عمل لهذا الدرس)."""
    return WorksheetRequest(
        kind="worksheet", topic=plan.topic, grade_level=plan.grade_level
    )
