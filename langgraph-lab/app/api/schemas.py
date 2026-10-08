"""نماذج الدخل/الخرج (Pydantic = تحقق صارم)."""

from datetime import datetime

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """جسم POST /chat (عام، توافق خلفي)."""

    message: str = Field(min_length=1, max_length=4000)
    thread_id: str = Field(default="default", min_length=1, max_length=64)


class ClarificationOut(BaseModel):
    """حقل الاستيضاح المهيكل للديلوج (بجانب reply النصي)."""

    kind: str = "plan"
    missing: list[str] = Field(default_factory=list)
    suggestions: dict[str, list[str]] = Field(default_factory=dict)
    profile_empty: bool = False


class ChatResponse(BaseModel):
    """رد POST /chat."""

    reply: str
    sources: list["SourceOut"] = Field(default_factory=list)
    clarification: ClarificationOut | None = None


class SourceOut(BaseModel):
    """مصدر واحد أُرسل للنموذج (شفافية الإنتاج)."""

    title: str = ""
    subject: str = ""
    lesson: str = ""
    text: str = ""


class ConversationCreate(BaseModel):
    """جسم POST /conversations."""

    title: str = Field(default="", max_length=60)


class MessageOut(BaseModel):
    """رسالة واحدة للعرض في الفرونت."""

    id: int
    role: str
    content: str
    created_at: datetime | None = None


class ConversationOut(BaseModel):
    """محادثة في القائمة: معاينة الأخيرة وعدد الرسائل."""

    id: int
    title: str
    message_count: int
    last_message: str = ""
    updated_at: datetime | None = None


class ConversationDetailOut(BaseModel):
    """سجل محادثة واحدة مع رسائلها."""

    id: int
    title: str
    messages: list[MessageOut]


class SendMessageIn(BaseModel):
    """جسم POST /conversations/{id}/messages."""

    message: str = Field(min_length=1, max_length=4000)


class SendMessageOut(BaseModel):
    """رد الإرسال: رد المساعد فقط (السجل يُجلب من GET)."""

    reply: str
    sources: list[SourceOut] = Field(default_factory=list)
    clarification: ClarificationOut | None = None


class TeacherCopyOut(BaseModel):
    """نسخة المعلم: نوع + نص معروض بالإجابات (لا تُحفظ كرسالة)."""

    kind: str
    text: str
