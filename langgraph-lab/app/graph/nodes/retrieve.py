"""سياق الاسترجاع: تنسيق مقاطع المعرفة كتعليم نظام (تنسيق فقط، بلا DB)."""

from app.graph.content import message_text


def format_knowledge_context(
    chunks: list[dict[str, object]], limit: int = 5
) -> str | None:
    """مقاطع ← تعليم نظام موجز أو None عند الفراغ."""
    parts: list[str] = []
    for chunk in chunks[: max(1, limit)]:
        title = str(chunk.get("title") or "").strip()
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        label = title or str(chunk.get("lesson") or "مقطع")
        parts.append(f"[{label}]: {text[:800]}")
    if not parts:
        return None
    return (
        "سياق من كتب المنهج (أجب منه أولاً وقدمه على معرفتك العامة).\n"
        "عند سؤالك عن مصادرك اذكر هذه العناوين فقط ولا تخترع أسماء كتب خارجية:\n"
        + "\n---\n".join(parts)
    )


def format_sources_block(
    chunks: list[dict[str, object]], limit: int = 5
) -> str | None:
    """مقاطع ← كتلة مصادر مرقمة للشفافية أو None عند الفراغ."""
    lines: list[str] = []
    for i, chunk in enumerate(chunks[: max(1, limit)], start=1):
        title = str(chunk.get("title") or "").strip()
        subject = str(chunk.get("subject") or "").strip()
        lesson = str(chunk.get("lesson") or "").strip()
        meta = " / ".join(p for p in (subject, lesson) if p)
        label = title or lesson or "مقطع"
        lines.append(f"{i}. {label}" + (f" ({meta})" if meta and meta != label else ""))
    if not lines:
        return None
    return "المصادر:\n" + "\n".join(lines)


def last_user_text(messages: list[object]) -> str:
    """رسائل الحالة ← نص آخر رسالة بشرية (فارغ عند الغياب)."""
    from langchain_core.messages import BaseMessage

    for message in reversed(messages):
        if isinstance(message, BaseMessage) and message.type == "human":
            return message_text(message.content)
    if messages:
        last = messages[-1]
        if isinstance(last, BaseMessage):
            return message_text(last.content)
    return ""


def build_search_query(messages: list[object], max_chars: int = 500) -> str:
    """رسائل الحالة ← استعلام يحمل السياق (آخر رسالتين بشريتين).

    الأسئلة اللاحقة مثل (ما إعرابه؟) بلا موضوع، فيضيع البحث؛
    دمج السؤال السابق يعيد الموضوع (الفاعل) للاستعلام.
    """
    from langchain_core.messages import BaseMessage

    humans: list[str] = []
    for message in reversed(messages):
        if isinstance(message, BaseMessage) and message.type == "human":
            text = message_text(message.content).strip()
            if text:
                humans.append(text)
            if len(humans) >= 2:
                break
    if not humans:
        return last_user_text(messages)
    query = " ".join(reversed(humans))
    return query[:max_chars].strip()
