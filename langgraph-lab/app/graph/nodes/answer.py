"""عقد الردود (تحية وإجابة ورفض)."""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage

from app.domain.ports import ChatModelPort, TeacherDirectoryPort
from app.domain.state import ChatState
from app.graph.nodes.profile import profile_ask_instruction
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
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع الإجابة: يغلق (Closure) على النموذج المحقون."""

    def _answer(state: ChatState) -> dict[str, list[BaseMessage]]:
        prompt = select_window(list(state["messages"]))
        snapshot = state.get("profile_snapshot")
        instruction = (
            profile_ask_instruction(dict(snapshot)) if isinstance(snapshot, dict) else None
        )
        if instruction is not None:
            prompt = [SystemMessage(content=instruction), *prompt]
        reply = model.invoke(prompt)
        reply.name = "answer"
        return {"messages": [reply]}

    return _answer


def make_decline_node() -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """عقدة الرفض: خارج النطاق ← رسالة ثابتة."""

    def _decline(_state: ChatState) -> dict[str, list[BaseMessage]]:
        return {"messages": [AIMessage(content="عذرا، هذا خارج نطاق مساعد المعلم.")]}  # noqa: ARG001

    return _decline
