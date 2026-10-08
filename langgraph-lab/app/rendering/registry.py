"""سجل المخرجات: نية الانتاج ← (المخطط، العارض)."""

from app.core.errors import AppError, ErrorCode
from app.domain.models import LessonPlan
from app.domain.outputs.quiz import QuizOutput
from app.domain.outputs.worksheet import WorksheetOutput
from app.rendering.lesson_plan import render_lesson_plan
from app.rendering.quiz_paper import render_quiz_output
from app.rendering.worksheet_paper import render_worksheet_output

StructuredOutput = QuizOutput | WorksheetOutput | LessonPlan
SchemaType = type[QuizOutput] | type[WorksheetOutput] | type[LessonPlan]

OUTPUT_SCHEMAS: dict[str, SchemaType] = {
    "generate_quiz": QuizOutput,
    "generate_worksheet": WorksheetOutput,
    "plan_lesson": LessonPlan,
}

SUPPORTED_INTENTS: tuple[str, ...] = tuple(OUTPUT_SCHEMAS)


def output_schema_for(intent: str) -> SchemaType:
    try:
        return OUTPUT_SCHEMAS[intent]
    except KeyError:
        raise ValueError("unsupported structured intent") from None


def render_for_intent(intent: str, output: object, show_answers: bool = False) -> str:
    schema = output_schema_for(intent)
    if not isinstance(output, schema):
        raise ValueError("output type mismatches intent")
    if isinstance(output, QuizOutput):
        return render_quiz_output(output, show_answers)
    if isinstance(output, WorksheetOutput):
        return render_worksheet_output(output, show_answers)
    return render_lesson_plan(output)


#: زر نسخة المعلم ← (حقل المسودة، المخطط)؛ العرض دائمًا بالإجابات وبلا توليد.
_TEACHER_DRAFTS: dict[str, tuple[str, type[QuizOutput] | type[WorksheetOutput]]] = {
    "quiz": ("quiz_draft", QuizOutput),
    "worksheet": ("worksheet_draft", WorksheetOutput),
}


def _coerce_draft(
    raw: object, schema: type[QuizOutput] | type[WorksheetOutput]
) -> QuizOutput | WorksheetOutput | None:
    if isinstance(raw, schema):
        return raw
    if isinstance(raw, dict):
        try:
            return schema.model_validate(raw)
        except Exception:
            return None
    return None


def render_teacher_copy(values: dict[str, object], kind: str) -> str:
    """قيم حالة الرسم + نوع ← نص نسخة المعلم (يُحفظ JSON لا Markdown)."""
    entry = _TEACHER_DRAFTS.get(kind.strip().lower())
    if entry is None:
        raise AppError(ErrorCode.VALIDATION_FAILED, "نوع النسخة غير معروف.", status=422)
    field, schema = entry
    draft = _coerce_draft(values.get(field), schema)
    if draft is None:
        raise AppError(ErrorCode.NOT_FOUND, "لا توجد نسخة معلم بعد.", status=404)
    if isinstance(draft, QuizOutput):
        return render_quiz_output(draft, show_answers=True)
    return render_worksheet_output(draft, show_answers=True)

