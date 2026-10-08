"""اعادة محاولة واحدة للمخرجات المهيكلة (سياسة موحدة).

القاعدة: محاولة ← فشل ← اعادة واحدة مع تلميح الخطأ ← فشل ← خطأ صريح
للمرشح العام. لا اصلاح صامت ولا سقوط لنص حر.
"""

from langchain_core.messages import BaseMessage, HumanMessage
from pydantic import BaseModel

from app.core.errors import AppError, ErrorCode
from app.core.trace import get_logger
from app.domain.ports import StructuredOutputPort

logger = get_logger(__name__)

#: سقف تلميح الخطأ حتى لا يتضخم موجه الاعادة.
_ERROR_HINT_LIMIT = 300


def _hint(exc: Exception) -> str:
    details = getattr(exc, "details", None)
    raw = str(details or exc).strip()
    return raw[:_ERROR_HINT_LIMIT]


def parse_with_retry[T: BaseModel](
    structured: StructuredOutputPort,
    prompt: list[BaseMessage],
    schema: type[T],
    what: str = "المخرجات",
) -> T:
    """محاولة ← إعادة بتلميح ← فشل ثانٍ يتحول لخطأ ودّي قابل لإعادة المحاولة يدويًا."""
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
        try:
            return structured.parse(retry_prompt, schema)
        except Exception as exc:
            hint = _hint(exc)
            logger.warning("structured_parse_failed what=%s hint=%s", what, hint)
            raise AppError(
                ErrorCode.INVALID_MODEL_OUTPUT,
                f"تعذر توليد {what} صالح، حاول مجددًا.",
                status=502,
            ) from exc

