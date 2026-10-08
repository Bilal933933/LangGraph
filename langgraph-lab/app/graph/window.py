"""نافذة السياق (Context Window = آخر N رسالة ترسل للنموذج).

الحافظ (Checkpointer) يحتفظ بالسجل الكامل لكل thread_id،
لكن النموذج يستقبل نافذة محدودة فقط حتى لا تتجاوز حد التوكن.
"""

from langchain_core.messages import BaseMessage

#: عدد الرسائل الأخيرة المرسلة للنموذج. الباقي يبقى في الحافظ فقط.
CONTEXT_WINDOW_MESSAGES = 20


def select_window(
    messages: list[BaseMessage], limit: int = CONTEXT_WINDOW_MESSAGES
) -> list[BaseMessage]:
    """آخر limit رسالة ← نافذة النموذج. فارغ أو أقل ← الكل.

    أمان Gemini: تُسقط القائدة غير البشرية حتى أول human حتى لا
    تبدأ النافذة بـ ai/tool ولا تُيتّم ToolMessage عن AIMessage(tool_calls).
    """
    if limit <= 0:
        return []
    if len(messages) <= limit:
        window = list(messages)
    else:
        start = len(messages) - limit
        while start > 0 and getattr(messages[start], "type", None) != "human":
            start -= 1
        window = list(messages[start : start + limit])
    for i, message in enumerate(window):
        if getattr(message, "type", None) == "human":
            return window[i:]
    return []
