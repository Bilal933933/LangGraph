"""احداث التقدم المخصصة (عقد بطيئة بلا بث رموز).

القاعدة: اشارة خفيفة فقط (عقدة + طور)، بلا نصوص ولا بيانات شخصية.
خارج البث المخصص تُتجاهل بصمت — لا تكسر المسارات غير الباثة.
"""

from app.core.trace import get_logger

logger = get_logger(__name__)


def emit(node: str, phase: str) -> None:
    try:
        from langgraph.config import get_stream_writer

        get_stream_writer()({"node": node, "phase": phase})
    except Exception as exc:
        logger.debug("progress_emit_skipped node=%s phase=%s error=%r", node, phase, exc)

