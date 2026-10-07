"""نماذج النطاق (Pydantic = تحقق صارم)."""

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal[
    "greeting",
    "general_question",
    "generate_quiz",
    "generate_worksheet",
    "plan_lesson",
    "unsupported",
    "update_profile",
]

#: كل النيات المعتمدة (مرجع واحد يمنع تشتت الأسماء).
INTENT_VALUES: tuple[str, ...] = (
    "greeting",
    "general_question",
    "generate_quiz",
    "generate_worksheet",
    "plan_lesson",
    "unsupported",
    "update_profile",
)

#: المسار الافتراضي عند فشل التصنيف.
DEFAULT_INTENT: Intent = "general_question"

#: نيات غامضة لا تقطع استكمال طلب ناقص (تُستخدم في router).
AMBIGUOUS_INTENTS: tuple[str, ...] = ("general_question", "unsupported", "greeting")


class TeacherContext(BaseModel):
    """سياق المعلم المحمّل حتميًا (DB ← Repository ← Node)."""

    name: str = ""
    subject: str = ""
    grades: list[str] = Field(default_factory=list)


class CanonicalRequest(BaseModel):
    """الطلب الموحد الصغير للتوجيه فقط (Request ≠ Message).

    Message = ماذا قال؟ Request = ماذا فهمنا؟
    يحتوي ما يلزم للتوجيه فقط، لا كل تفاصيل التنفيذ
    حتى لا يتحول Parser إلى God Object (كائن متضخم).
    التفاصيل (عدد الأهداف، نوع النشاط) تستخرج داخل Workflow.
    parent_request_id = سلسلة Revision (إصدار) للطلب الفعلي
    عبر الرسائل: Request B يعدل Request A ولا ينشئ دائما جديدا.
    """

    intent: Intent
    task: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    topic: str | None = Field(default=None, min_length=1)
    missing: list[str] = Field(default_factory=list)
    parent_request_id: str | None = Field(default=None, min_length=1)
    schema_version: Literal["v1"] = "v1"


class IntentResult(BaseModel):
    """نتيجة التصنيف المهيكلة من النموذج."""

    intent: Intent


class QuizRequest(BaseModel):
    """معاملات طلب الاختبار (الحقول فارغة = ناقصة)."""

    topic: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    num_questions: int | None = Field(default=None, gt=0, le=50)
    question_types: list[str] = Field(default_factory=list)


class WorksheetRequest(BaseModel):
    """معاملات طلب ورقة العمل/النشاط (الفارغ = ناقص، عدا kind له افتراضي).

    kind يُستنتج من النص (ورقة/تمارين ← worksheet، نشاط/لعبة صفية ← activity).
    num_items وminutes اختياريان (افتراضهما عند الكتابة 8 و15).
    """

    kind: Literal["worksheet", "activity"] | None = None
    topic: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    num_items: int | None = Field(default=None, gt=0, le=30)
    minutes: int | None = Field(default=None, gt=0, le=90)


class ProfileName(BaseModel):
    """الاسم المستخرج من قول المعلم (فارغ = لم يذكر اسما)."""

    name: str | None = Field(default=None, min_length=1)


class ProfileInfo(BaseModel):
    """حقول الملف المستخرجة من قول المعلم (الفارغ = لم يذكر)."""

    name: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    grades: list[str] = Field(default_factory=list)


class LessonRequest(BaseModel):
    """معاملات طلب التحضير (الحقول فارغة = ناقصة)."""

    topic: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    minutes: int | None = Field(default=None, gt=0, le=180)


class LessonSection(BaseModel):
    """قسم واحد من خطة الدرس ينتجه عامل متخصص."""

    kind: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)


class LessonPlan(BaseModel):
    """الخطة النهائية بعد الدمج والتحقق."""

    topic: str = Field(min_length=1)
    grade_level: str = Field(min_length=1)
    minutes: int = Field(gt=0, le=180)
    objectives: str = Field(default="")
    intro: str = Field(default="")
    steps: str = Field(default="")
    activities: str = Field(default="")
    assessment: str = Field(default="")


class ClarificationOut(BaseModel):
    """حقل الاستيضاح المهيكل للديلوج (بجانب reply النصي)."""

    kind: Literal["plan"] = "plan"
    missing: list[str] = Field(default_factory=list)
    suggestions: dict[str, list[str]] = Field(default_factory=dict)
    profile_empty: bool = False
