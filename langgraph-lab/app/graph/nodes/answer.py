"""عقد الردود (إجابة ورفض + مسار تحية المحادثة)."""

from collections.abc import Callable, Coroutine
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.core.config import get_settings
from app.core.trace import get_logger, preview, stage
from app.domain.ports import ChatModelPort, KnowledgeSearchPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.profile import profile_ask_instruction
from app.graph.nodes.retrieve import (
    build_search_query,
    format_knowledge_context,
    format_sources_block,
)
from app.graph.prompts.runtime.answer import ANSWER_SYSTEM
from app.graph.prompts.runtime.greeting import GREETING_SYSTEM
from app.graph.window import select_window
from app.rendering.general import render_general


def _is_greeting(state: ChatState) -> bool:
    """الحالة ← True عند نية تحية فقط (نظام محادثة لا رد منفصل)."""
    if state.get("intent") == "greeting":
        return True
    raw: object = state.get("canonical_request")
    intent = getattr(raw, "intent", None)
    if isinstance(intent, str) and intent == "greeting":
        return True
    if isinstance(raw, dict) and raw.get("intent") == "greeting":
        return True
    return False


def _teacher_name(state: ChatState) -> str:
    """اللقطة أو السياق المحمل ← اسم المعلم أو فارغ."""
    snapshot = state.get("profile_snapshot")
    if isinstance(snapshot, dict):
        name = str(snapshot.get("name") or "").strip()
        if name:
            return name[:100]
    runtime = state.get("runtime_context")
    name = getattr(runtime, "name", "")
    return str(name or "").strip()[:100]


async def _answer_greeting(
    state: ChatState,
    model: ChatModelPort,
    config: RunnableConfig | None,
) -> dict[str, object]:
    """مسار التحية: نموذج + نافذة السياق فقط، بلا معرفة وبلا مصادر."""
    logger = get_logger()
    prompt = select_window(list(state["messages"]))
    name = _teacher_name(state)
    instruction = GREETING_SYSTEM
    if name:
        instruction += f" اسم المعلم: {name}."
    prompt = [SystemMessage(content=instruction), *prompt]
    logger.info("stage=answer.greeting window=%d has_name=%s", len(prompt), bool(name))
    callbacks: Any = config.get("callbacks") if config is not None else None
    parts = [delta async for delta in model.astream(prompt, callbacks=callbacks)]
    reply = AIMessage(content="".join(parts).strip() or "أهلاً بك! كيف أقدر أساعدك اليوم؟")
    reply.name = "answer"
    return {"messages": [reply], "retrieved_sources": []}


def make_answer_node(
    model: ChatModelPort,
    knowledge: KnowledgeSearchPort | None = None,
    limit: int | None = None,
) -> Callable[..., Coroutine[Any, Any, dict[str, object]]]:
    """مصنع الإجابة: يغلق (Closure) على النموذج ومستودع المعرفة الاختياري."""

    async def _answer(
        state: ChatState, config: RunnableConfig | None = None
    ) -> dict[str, object]:
        if _is_greeting(state):
            return await _answer_greeting(state, model, config)
        logger = get_logger()
        with stage(logger, "answer.build_prompt", history=len(state["messages"])):
            prompt = select_window(list(state["messages"]))
        snapshot = state.get("profile_snapshot")
        instruction = (
            profile_ask_instruction(dict(snapshot)) if isinstance(snapshot, dict) else None
        )
        if instruction is not None:
            prompt = [SystemMessage(content=instruction), *prompt]
        eff = limit if limit is not None else get_settings().answer_retrieval_limit
        chunks: list[dict[str, object]] = []
        if knowledge is not None:
            try:
                hybrid = getattr(knowledge, "search_hybrid", None)
                if callable(hybrid):
                    chunks = hybrid(build_search_query(list(state["messages"])), eff)
                else:
                    chunks = knowledge.search(build_search_query(list(state["messages"])), eff)
                context = format_knowledge_context(chunks, limit=eff)
            except Exception:
                chunks = []
                context = None
            if context is not None:
                prompt = [SystemMessage(content=context), *prompt]
                logger.info("stage=answer.knowledge chunks=%d", len(chunks))
        prompt = [SystemMessage(content=ANSWER_SYSTEM), *prompt]
        logger.info(
            "stage=answer.prompt_ready window=%d has_profile_instruction=%s",
            len(prompt),
            instruction is not None,
        )
        with stage(logger, "answer.model_invoke", prompt_messages=len(prompt)):
            callbacks: Any = config.get("callbacks") if config is not None else None
            parts = [delta async for delta in model.astream(prompt, callbacks=callbacks)]
        reply = AIMessage(content="".join(parts))
        reply.name = "answer"
        logger.info(
            "stage=answer.reply chars=%d preview=%s",
            len(str(reply.content)),
            preview(reply.content),
        )
        sources = [
            {
                "title": str(c.get("title") or "").strip(),
                "subject": str(c.get("subject") or "").strip(),
                "lesson": str(c.get("lesson") or "").strip(),
                "text": str(c.get("text") or "").strip()[:1500],
            }
            for c in chunks[:eff]
            if str(c.get("text") or "").strip()
        ]
        block = format_sources_block(chunks, limit=eff)
        reply.content = render_general(message_text(reply.content), block)
        return {"messages": [reply], "retrieved_sources": sources}

    return _answer


def make_decline_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة الرفض: خارج النطاق ← رسالة ثابتة."""

    def _decline(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="عذرا، هذا خارج نطاق مساعد المعلم.")]}  # noqa: ARG001

    return _decline
