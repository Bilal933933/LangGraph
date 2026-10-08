"""مخرج ورقة العمل والنشاط (شكل صارم يغذي Renderer)."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

WorksheetKind = Literal["worksheet", "activity"]
Differentiation = Literal["core", "support", "enrichment"]


class WorksheetItem(BaseModel):
    instruction: str = Field(min_length=1)
    expected_answer: str = Field(default="")
    differentiation: Differentiation = "core"
    minutes: int = Field(default=0, ge=0, le=90)

    @field_validator("instruction", "expected_answer")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()


class WorksheetOutput(BaseModel):
    kind: WorksheetKind = "worksheet"
    topic: str = Field(min_length=1)
    grade_level: str = Field(min_length=1)
    items: list[WorksheetItem] = Field(min_length=1, max_length=30)
    minutes: int | None = Field(default=None, ge=0, le=90)
    schema_version: Literal["v1"] = "v1"

    @model_validator(mode="after")
    def _check_blank(self) -> "WorksheetOutput":
        if any(not item.instruction for item in self.items):
            raise ValueError("empty instruction")
        return self

