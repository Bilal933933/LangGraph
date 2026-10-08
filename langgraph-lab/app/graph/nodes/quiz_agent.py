"""وكيل الاختبارات (Quiz Agent = نموذج + أداة الدروس + حلقة قرار).

قاعدة الفصل: هذا الملف لوكيل الاختبارات فقط. أي وكيل جديد
(مناهج، تقييم، ...) ينشأ في ملف `*_agent.py` خاص به مع أدواته
وحلقته، ولا يضاف هنا أبدا.
"""

from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from app.domain.models import LessonPlan
from app.domain.outputs.quiz import QuizOutput
from app.domain.ports import ChatModelPort, StructuredOutputPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.profile import profile_ask_instruction
from app.graph.nodes.quiz_bridge import build_quiz_shape_prompt
from app.graph.nodes.structured_retry import parse_with_retry
from app.graph.progress import emit as emit_progress
from app.graph.prompts.runtime.quiz import QUIZ_AGENT_SYSTEM
from app.graph.window import select_window
from app.rendering.registry import render_for_intent


def _coerce_plan(raw: object) -> LessonPlan | None:
    """لقطة خطة (كائن أو قاموس بعد التسلسل) ← LessonPlan أو None."""
    if isinstance(raw, LessonPlan):
        return raw
    if isinstance(raw, dict):
        try:
            return LessonPlan(**{k: raw.get(k) for k in LessonPlan.model_fields})
        except Exception:
            return None
    return None


def make_quiz_agent_node(
    model: ChatModelPort,
    structured: StructuredOutputPort | None = None,
) -> Callable[..., dict[str, object]]:
    """مصنع وكيل الاختبارات: يغلق على نموذج مربوط بأدوات الاختبارات فقط.

    مع structured ← توليد مهيكل + حفظ quiz_draft + رد نسخة الطالب (بلا إجابات).
    بدونه ← مسار النص الحر القديم (توافق خلفي).
    """

    def _prompt(state: ChatState) -> tuple[list[BaseMessage], str]:
        request = state.get("quiz_request")
        topic = request.topic if request and request.topic else ""
        plan = _coerce_plan(state.get("plan_draft"))
        shape = build_quiz_shape_prompt(request, plan)
        messages = list(state["messages"])
        last_text = message_text(messages[-1].content) if messages else ""
        tail = messages[:-1] if messages and messages[-1].type == "human" else messages
        history = select_window(tail, 4)
        prompt: list[BaseMessage] = [
            SystemMessage(content=QUIZ_AGENT_SYSTEM),
            SystemMessage(content=shape),
        ]
        snapshot = state.get("profile_snapshot")
        if isinstance(snapshot, dict):
            instruction = profile_ask_instruction(dict(snapshot))
            if instruction is not None:
                prompt.append(SystemMessage(content=instruction))
        prompt += [
            HumanMessage(content=f"ولد اختبارا عن: {topic or last_text}"),
            *history,
        ]
        return prompt, topic or last_text

    def _quiz_agent(
        state: ChatState, config: RunnableConfig | None = None
    ) -> dict[str, object]:
        emit_progress("quiz_agent", "start")
        prompt, _ = _prompt(state)
        callbacks: Any = config.get("callbacks") if config is not None else None
        reply = model.invoke(prompt, callbacks=callbacks)
        reply.name = "quiz_agent"
        if structured is None or getattr(reply, "tool_calls", None):
            return {"messages": [reply]}
        emit_progress("quiz_agent", "shaping")
        quiz = parse_with_retry(
            structured,
            [
                SystemMessage(content="حول نص الاختبار التالي إلى المخطط بدقة."),
                HumanMessage(content=message_text(reply.content)),
            ],
            QuizOutput,
            what="اختبار",
        )
        paper = AIMessage(content=render_for_intent("generate_quiz", quiz))
        paper.name = "quiz_agent"
        return {"messages": [paper], "quiz_draft": quiz}

    return _quiz_agent
