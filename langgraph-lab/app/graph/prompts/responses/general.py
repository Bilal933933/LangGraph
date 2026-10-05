"""قالب الرسالة العامة (عرض فقط)."""


def render_general(reply: str, sources_block: str | None) -> str:
    """نص نظيف + كتلة مصادر ← نص نهائي للمعلم."""
    cleaned = reply.strip()
    if not cleaned:
        return "تعذر التوليد."
    if sources_block is None or not sources_block.strip():
        return cleaned
    return f"{cleaned}\n\n---\n{sources_block.strip()}"
