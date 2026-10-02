"""الحالة (State = الذاكرة المشتركة بين العقد)."""

from typing import Annotated, NotRequired

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ChatState(TypedDict):
    """حالة المرحلة 2: رسائل + نية للتوجيه الشرطي.

    add_messages = مخفّض (Reducer) يدمج الرسائل الجديدة مع القديمة
    بدل استبدالها.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    intent: NotRequired[str]
