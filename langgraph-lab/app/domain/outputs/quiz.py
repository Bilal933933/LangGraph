"""مخرج الاختبار المهيكل (شكل صارم يغذي Renderer)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

QuizQuestionType = Literal["mcq", "true_false", "short_answer"]


class QuizQuestion(BaseModel):
    type: QuizQuestionType
    stem: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    answer_index: int | None = None
    explanation: str = Field(default="")
    points: int = Field(default=0, ge=0, le=100)

    @field_validator("options")
    @classmethod
    def _strip_options(cls, values: list[str]) -> list[str]:
        return [str(option).strip() for option in values if str(option).strip()]

    @model_validator(mode="after")
    def _check_shape(self) -> "QuizQuestion":
        if self.type == "mcq" and len(self.options) != 4:
            raise ValueError("mcq needs 4 options")
        if self.type == "true_false" and len(self.options) != 2:
            raise ValueError("true_false needs 2 options")
        if self.type == "short_answer" and self.options:
            raise ValueError("short_answer has no options")
        if self.type in ("mcq", "true_false"):
            if self.answer_index is None:
                raise ValueError("answer_index required")
            if not 0 <= self.answer_index < len(self.options):
                raise ValueError("answer_index out of range")
        if len(set(self.options)) != len(self.options):
            raise ValueError("duplicate options")
        return self


class QuizOutput(BaseModel):
    topic: str = Field(min_length=1)
    grade_level: str = Field(min_length=1)
    questions: list[QuizQuestion] = Field(min_length=1, max_length=50)
    schema_version: Literal["v1"] = "v1"

    @model_validator(mode="after")
    def _check_total(self) -> "QuizOutput":
        total = sum(question.points for question in self.questions)
        if total > 100:
            raise ValueError("total points over 100")
        return self

