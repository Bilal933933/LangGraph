"""قالب ورقة الاختبار (عرض فقط)."""

from app.domain.models import QuizRequest


def render_quiz_paper(request: QuizRequest | None, body: str) -> str:
    """طلب + نص الأسئلة ← ورقة نهائية بترويسة ثابتة ودرجات."""
    topic = request.topic if request and request.topic else "غير محدد"
    grade = request.grade_level if request and request.grade_level else "غير محدد"
    num = request.num_questions if request and request.num_questions else ""
    header = f"اختبار: {topic} ({grade}) — عدد الأسئلة: {num} — المجموع: 100"
    instructions = "التعليمات: أجب عن جميع الأسئلة، وعلل إجابات الصح/خطأ بسطر واحد."
    return f"{header}\n\n{instructions}\n\n{body.strip()}"
