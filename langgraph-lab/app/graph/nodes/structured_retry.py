"""اعادة محاولة واحدة للمخرجات المهيكلة (سياسة موحدة).

القاعدة: محاولة ← فشل ← اعادة واحدة مع تلميح الخطأ ← فشل ← خطأ صريح
للمرشح العام. لا اصلاح صامت ولا سقوط لنص حر.
"""

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from app.domain.ports import StructuredOutputPort

#: سقف تلميح الخطأ حتى لا يتضخم موجه الاعادة.
_ERROR_HINT_LIMIT = 300


def _hint(exc: Exception) -> str:
    details = getattr(exc, "details", None)
    raw = str(details or exc).strip()
    return raw[:_ERROR_HINT_LIMIT]


def parse_with_retry[T: BaseModel](
    structured: StructuredOutputPort, prompt: list[BaseMessage], schema: type[T]
) -> T:
    try:
        return structured.parse(prompt, schema)
    except Exception as first:
        retry_prompt = [
            *prompt,
            HumanMessage(
                content="المخرج السابق مرفوض: "
                + _hint(first)
                + ". اعد الاخراج بنفس المخطط فقط، بلا شرح."
            ),
        ]
        return structured.parse(retry_prompt, schema)

