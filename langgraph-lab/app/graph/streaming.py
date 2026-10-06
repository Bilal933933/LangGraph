"""بث الرسم: updates ← مراحل، messages ← رموز، values ← الحالة النهائية."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from langchain_core.messages import AIMessageChunk

from app.core.trace import get_logger
from app.graph.content import message_text

logger = get_logger(__name__)

StreamEvent = dict[str, object]

_STREAM_MODES = ["updates", "messages", "values"]


def invoke_sync(
    graph: Any, payload: dict[str, object], config: dict[str, object]
) -> dict[str, object]:
    """invoke متزامن فوق ainvoke (يدعم العقد async — المسارات غير الباثة)."""
    result = asyncio.run(graph.ainvoke(payload, config))
    assert isinstance(result, dict)
    return result


def encode_sse(event: StreamEvent) -> str:
    """حدث ← إطار SSE نصي (event + data + سطران)."""
    etype = str(event.get("type", "message"))
    return f"event: {etype}\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"


def _token_parts(data: Any) -> tuple[str, str]:
    """قطعة messages ← (نص، عقدة)؛ الكاملة تُتخطى (نصها يأتي في done)."""
    message, meta = data
    if not isinstance(message, AIMessageChunk):
        return "", ""
    text = message_text(message.content)
    node = ""
    if isinstance(meta, dict):
        node = str(meta.get("langgraph_node", "") or "")
    return text, node


async def stream_run(
    graph: Any, payload: dict[str, object], config: dict[str, object]
) -> AsyncIterator[StreamEvent]:
    """يبث المراحل والرموز ثم done بالحالة النهائية؛ أي عطل ← حدث error."""
    try:
        final: dict[str, object] = {}
        async for mode, data in graph.astream(payload, config, stream_mode=_STREAM_MODES):
            if mode == "updates" and isinstance(data, dict):
                for node in data:
                    yield {"type": "stage", "node": str(node)}
            elif mode == "messages":
                text, node = _token_parts(data)
                if text != "":
                    yield {"type": "token", "node": node, "text": text}
            elif mode == "values" and isinstance(data, dict):
                final = data
        yield {"type": "done", "state": final}
    except Exception as exc:
        logger.exception("stream_run_failed error=%r", exc)
        yield {"type": "error", "message": "تعذر البث الآن."}
