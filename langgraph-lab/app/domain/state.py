"""الحالة (State = الذاكرة المشتركة بين العقد)."""

from typing import Annotated, NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from app.domain.models import Intent, QuizRequest


class ChatState(TypedDict):
    """حالة مولد الاختبارات: رسائل + نية + طلب + نواقص.

    add_messages = مخفّض (Reducer) يدمج الرسائل الجديدة مع القديمة
    بدل استبدالها.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    intent: NotRequired[Intent]
    quiz_request: NotRequired[QuizRequest]
    missing_fields: NotRequired[list[str]]
