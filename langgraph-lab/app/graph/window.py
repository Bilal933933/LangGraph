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
    """آخر limit رسالة ← نافذة النموذج. فارغ أو أقل ← الكل."""
    if limit <= 0:
        return []
    if len(messages) <= limit:
        return list(messages)
    return list(messages[-limit:])
