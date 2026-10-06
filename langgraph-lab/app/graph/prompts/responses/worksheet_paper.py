"""قالب ورقة العمل والنشاط (عرض فقط)."""

from app.domain.models import WorksheetRequest


def render_worksheet_paper(request: WorksheetRequest | None, body: str) -> str:
    """طلب + نص التمارين ← ورقة نهائية بترويسة ثابتة ومفتاح إجابة."""
    kind = request.kind if request and request.kind else "worksheet"
    topic = request.topic if request and request.topic else "غير محدد"
    grade = request.grade_level if request and request.grade_level else "غير محدد"
    if kind == "activity":
        minutes = request.minutes if request and request.minutes else 15
        header = f"نشاط صفي: {topic} ({grade}) — الزمن: {minutes} دقيقة"
    else:
        num = request.num_items if request and request.num_items else 8
        header = f"ورقة عمل: {topic} ({grade}) — عدد التمارين: {num}"
    instructions = "التعليمات: اكتب اسمك والتاريخ، وأجب عن جميع التمارين بالترتيب."
    return f"{header}\n\n{instructions}\n\n{body.strip()}"
