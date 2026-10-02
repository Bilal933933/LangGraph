"""الحالة (State = الذاكرة المشتركة بين العقد)."""

from typing import Annotated

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class ChatState(TypedDict):
    """حالة المرحلة 1: قائمة رسائل فقط.

    add_messages = مخفّض (Reducer) يدمج الرسائل الجديدة مع القديمة
    بدل استبدالها.
    """

    messages: Annotated[list[BaseMessage], add_messages]
