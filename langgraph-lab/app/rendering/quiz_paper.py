"""قالب ورقة الاختبار (عرض فقط، حتمي بلا LLM)."""

from app.domain.models import QuizRequest
from app.domain.outputs.quiz import QuizOutput

#: ترجمة أنواع الأسئلة للعناوين الظاهرة (النموذج ينتج مفاتيح إنجليزية فقط).
TYPE_LABELS: dict[str, str] = {
    "mcq": "اختيار من متعدد",
    "true_false": "صح/خطأ",
    "short_answer": "مقالي قصير",
}

#: حروف الخيارات الثابتة (أ، ب، ج، د) — لا تحسب من يونيكود (الثالثة ة لا ج).
OPTION_LETTERS: tuple[str, ...] = ("أ", "ب", "ج", "د")


def render_quiz_paper(request: QuizRequest | None, body: str) -> str:
    """طلب + نص الأسئلة ← ورقة نهائية (legacy: للنص الحر قبل الهجرة الكاملة)."""
    topic = request.topic if request and request.topic else "غير محدد"
    grade = request.grade_level if request and request.grade_level else "غير محدد"
    num = request.num_questions if request and request.num_questions else ""
    header = f"اختبار: {topic} ({grade}) — عدد الأسئلة: {num} — المجموع: 100"
    instructions = "التعليمات: أجب عن جميع الأسئلة، وعلل إجابات الصح/خطأ بسطر واحد."
    return f"{header}\n\n{instructions}\n\n{body.strip()}"


def _render_question(index: int, question_dict: dict[str, object], show_answers: bool) -> str:
    """سؤال واحد ← أسطر مرقمة، والحجب في الخادم (لا إجابة ولا شرح عند False)."""
    stem = str(question_dict.get("stem") or "").strip()
    raw_options = question_dict.get("options")
    options = list(raw_options) if isinstance(raw_options, list) else []
    points = question_dict.get("points") or 0
    label = TYPE_LABELS.get(str(question_dict.get("type") or ""), "")
    head = f"س{index}: {stem}"
    if points:
        head += f" ({points} درجات)"
    if label:
        head += f" [{label}]"
    lines = [head]
    for option_pos, option in enumerate(options):
        letter = (
            OPTION_LETTERS[option_pos] if option_pos < len(OPTION_LETTERS) else str(option_pos + 1)
        )
        lines.append(f"  {letter}) {option}")
    if show_answers:
        answer_index = question_dict.get("answer_index")
        if isinstance(answer_index, int) and 0 <= answer_index < len(options):
            lines.append(f"  الإجابة: {options[answer_index]}")
        explanation = str(question_dict.get("explanation") or "").strip()
        if explanation:
            lines.append(f"  الشرح: {explanation}")
    return "\n".join(lines)


def _display_points(quiz: QuizOutput) -> list[int]:
    """درجات العرض: المعينة كما هي، والتوزيع المتساوي (100/n) عند غيابها كلها."""
    points = [question.points for question in quiz.questions]
    if any(points):
        return points
    count = len(points)
    share, rest = divmod(100, count)
    return [share + (1 if pos < rest else 0) for pos in range(count)]


def render_quiz_output(quiz: QuizOutput, show_answers: bool = False) -> str:
    """اختبار متحقق منه ← ورقة نهائية (نسخة الطالب/المعلم عبر show_answers)."""
    shown = _display_points(quiz)
    total = sum(shown)
    header = (
        f"اختبار: {quiz.topic} ({quiz.grade_level})"
        f" — عدد الأسئلة: {len(quiz.questions)} — المجموع: {total}"
    )
    instructions = "التعليمات: أجب عن جميع الأسئلة، وعلل إجابات الصح/خطأ بسطر واحد."
    body = "\n\n".join(
        _render_question(pos, {**question.model_dump(), "points": pts}, show_answers)
        for pos, (question, pts) in enumerate(zip(quiz.questions, shown, strict=True), start=1)
    )
    return f"{header}\n\n{instructions}\n\n{body}"
