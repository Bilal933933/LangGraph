"""جسر الاختبار من الخطة (منطق فقط، لا برومبتات هنا)."""

from app.domain.models import LessonPlan, QuizRequest
from app.graph.prompts.runtime.quiz_shape import QUIZ_SHAPE_SYSTEM


def build_quiz_shape_prompt(request: QuizRequest | None, plan: LessonPlan | None = None) -> str:
    """طلب + خطة اختيارية ← نص شكل ملزم يدمج في prompt الوكيل."""
    num = request.num_questions if request and request.num_questions else 5
    topic = request.topic if request and request.topic else (plan.topic if plan else "")
    grade = request.grade_level if request and request.grade_level else ""
    if plan and not grade:
        grade = plan.grade_level
    types = list(request.question_types) if request and request.question_types else []
    lines = [
        QUIZ_SHAPE_SYSTEM,
        f"الموضوع: {topic or 'غير محدد'} — الصف: {grade or 'غير محدد'} — العدد: {num}",
    ]
    if types:
        lines.append("الأنواع المطلوبة صراحة: " + "، ".join(types))
    if plan and plan.objectives.strip():
        lines.append("أهداف الخطة (غط كل هدف بسؤال على الأقل):\n" + plan.objectives.strip())
    return "\n".join(lines)


def quiz_request_from_plan(plan: LessonPlan, num_questions: int = 5) -> QuizRequest:
    """خطة درس ← طلب اختبار جاهز لزر (أنشئ اختبارا لهذا الدرس)."""
    total = max(1, min(int(num_questions), 50))
    return QuizRequest(topic=plan.topic, grade_level=plan.grade_level, num_questions=total)
