"""مخرجات مهيكلة متحقق منها (Pydantic = شكل صارم)."""

from app.domain.outputs.quiz import QuizOutput, QuizQuestion
from app.domain.outputs.worksheet import WorksheetItem, WorksheetOutput

__all__ = ["QuizOutput", "QuizQuestion", "WorksheetItem", "WorksheetOutput"]

