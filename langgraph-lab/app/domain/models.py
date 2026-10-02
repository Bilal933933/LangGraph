"""نماذج النطاق (Pydantic = تحقق صارم)."""

from typing import Literal

from pydantic import BaseModel, Field

Intent = Literal["greeting", "general_question", "generate_quiz", "unsupported"]


class IntentResult(BaseModel):
    """نتيجة التصنيف المهيكلة من النموذج."""

    intent: Intent


class QuizRequest(BaseModel):
    """معاملات طلب الاختبار (الحقول فارغة = ناقصة)."""

    topic: str | None = Field(default=None, min_length=1)
    grade_level: str | None = Field(default=None, min_length=1)
    num_questions: int | None = Field(default=None, gt=0, le=50)
    question_types: list[str] = Field(default_factory=list)
