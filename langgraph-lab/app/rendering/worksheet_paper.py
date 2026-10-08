"""قالب ورقة العمل والنشاط (عرض فقط، حتمي بلا LLM)."""

from app.domain.models import WorksheetRequest
from app.domain.outputs.worksheet import WorksheetOutput

#: وسوم التمايز الظاهرة (معلومة توزيع لا إجابة، تظهر في النسختين).
DIFF_LABELS: dict[str, str] = {"support": "دعم", "enrichment": "إثراء"}


def render_worksheet_paper(request: WorksheetRequest | None, body: str) -> str:
    """طلب + نص التمارين ← ورقة نهائية (legacy: للنص الحر قبل الهجرة الكاملة)."""
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


def _render_item(index: int, item_dict: dict[str, object]) -> str:
    """تمرين واحد ← سطر مرقم مع وسم التمايز (بلا إجابات هنا أبدًا)."""
    instruction = str(item_dict.get("instruction") or "").strip()
    line = f"{index}) {instruction}"
    minutes = item_dict.get("minutes") or 0
    if isinstance(minutes, int) and minutes > 0:
        line += f" — {minutes} د"
    tag = DIFF_LABELS.get(str(item_dict.get("differentiation") or ""))
    if tag:
        line += f" [{tag}]"
    return line


def render_worksheet_output(worksheet: WorksheetOutput, show_answers: bool = False) -> str:
    """ورقة متحقق منها ← نص نهائي (مفتاح الإجابة للمعلم فقط عبر show_answers)."""
    if worksheet.kind == "activity":
        minutes = worksheet.minutes if worksheet.minutes else 15
        header = f"نشاط صفي: {worksheet.topic} ({worksheet.grade_level}) — الزمن: {minutes} دقيقة"
    else:
        header = (
            f"ورقة عمل: {worksheet.topic} ({worksheet.grade_level})"
            f" — عدد التمارين: {len(worksheet.items)}"
        )
    instructions = "التعليمات: اكتب اسمك والتاريخ، وأجب عن جميع التمارين بالترتيب."
    body = "\n".join(
        _render_item(pos, item.model_dump()) for pos, item in enumerate(worksheet.items, start=1)
    )
    text = f"{header}\n\n{instructions}\n\n{body}"
    if show_answers:
        key_lines = [
            f"{pos}) {item.expected_answer.strip() or '—'}"
            for pos, item in enumerate(worksheet.items, start=1)
        ]
        text += "\n\nمفتاح الإجابة للمعلم:\n" + "\n".join(key_lines)
    return text
