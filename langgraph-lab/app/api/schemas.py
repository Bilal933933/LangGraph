"""نماذج الدخل/الخرج (Pydantic = تحقق صارم)."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """جسم POST /chat."""

    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    """رد POST /chat."""

    reply: str
