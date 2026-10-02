"""استخراج النص الصالح للعرض من محتوى رسائل LangChain."""


def message_text(content: object) -> str:
    """محتوى رسالة (نص أو قائمة كتل) ← نص صالح للعرض فقط.

    موديلات Gemini الحديثة تعيد مع الرد كتل تفكير (Thinking Blocks)
    مثل بصمات التفكير — هذه الدالة تتجاهلها وتبقي النص فقط.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                if block.strip():
                    parts.append(block)
            elif isinstance(block, dict):
                text: object = block.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return " ".join(parts)
    return str(content)
