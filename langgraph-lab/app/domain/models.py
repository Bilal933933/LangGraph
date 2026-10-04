"""نماذج النطاق (Pydantic = تحقق صارم)."""

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["greeting", "general_question", "generate_quiz", "unsupported", "update_profile"]


class IntentResult(BaseModel):
    """نتيجة التصنيف المهيكلة من النموذج."""

    intent: Intent


class QuizRequest(BaseModel):
    """معاملات طلب الاختبار (الحقول فارغة = ناقصة)."""

    topic: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    num_questions: int | None = Field(default=None, gt=0, le=50)
    question_types: list[str] = Field(default_factory=list)


class ProfileName(BaseModel):
    """الاسم المستخرج من قول المعلم (فارغ = لم يذكر اسما)."""

    name: str | None = Field(default=None, min_length=1)


class ProfileInfo(BaseModel):
    """حقول الملف المستخرجة من قول المعلم (الفارغ = لم يذكر)."""

    name: str | None = Field(default=None, min_length=1)
    subject: str | None = Field(default=None, min_length=1)
    grades: list[str] = Field(default_factory=list)
