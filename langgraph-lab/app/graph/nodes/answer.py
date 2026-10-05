"""عقد الردود (تحية وإجابة ورفض)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from app.core.config import get_settings
from app.core.trace import get_logger, preview, stage
from app.domain.ports import ChatModelPort, KnowledgeSearchPort, TeacherDirectoryPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.profile import profile_ask_instruction
from app.graph.nodes.retrieve import (
    build_search_query,
    format_knowledge_context,
    format_sources_block,
)
from app.graph.prompts.responses.general import render_general
from app.graph.window import select_window


def make_greeting_node(
    directory: TeacherDirectoryPort | None = None,
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة التحية الأولى فقط: رد سريع بلا LLM.

    الجلب كسول (Lazy): لا تستعلم عن الاسم إلا إذا وصل المسار إلى
    greeting وكان teacher_id موجودا. غياب أو فشل ← تحية عامة.
    المتابعة (تحية ثانية في نفس الجلسة) لا تأتي هنا أصلا، بل
    يوجهها route_by_intent إلى answer ليرد النموذج من نافذة السياق.
    """

    def _greet(state: ChatState) -> dict[str, list[BaseMessage]]:
        teacher_id = state.get("teacher_id")
        name: str | None = None
        if directory is not None and isinstance(teacher_id, int):
            try:
                name = directory.get_name(teacher_id)
            except Exception:
                name = None
        if name and name.strip():
            text = f"أهلاً {name.strip()}! كيف أقدر أساعدك اليوم؟"
            return {"messages": [AIMessage(content=text)]}
        return {"messages": [AIMessage(content="أهلاً بك! كيف أقدر أساعدك اليوم؟")]}

    return _greet


def make_answer_node(
    model: ChatModelPort,
    knowledge: KnowledgeSearchPort | None = None,
    limit: int | None = None,
) -> Callable[[ChatState], dict[str, object]]:
    """مصنع الإجابة: يغلق (Closure) على النموذج ومستودع المعرفة الاختياري."""

    def _answer(state: ChatState) -> dict[str, object]:
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
        logger.info(
            "stage=answer.prompt_ready window=%d has_profile_instruction=%s",
            len(prompt),
            instruction is not None,
        )
        with stage(logger, "answer.model_invoke", prompt_messages=len(prompt)):
            reply = model.invoke(prompt)
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
