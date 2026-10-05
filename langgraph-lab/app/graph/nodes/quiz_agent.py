"""وكيل الاختبارات (Quiz Agent = نموذج + أداة الدروس + حلقة قرار).

قاعدة الفصل: هذا الملف لوكيل الاختبارات فقط. أي وكيل جديد
(مناهج، تقييم، ...) ينشأ في ملف `*_agent.py` خاص به مع أدواته
وحلقته، ولا يضاف هنا أبدا.
"""

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.domain.models import LessonPlan
from app.domain.ports import ChatModelPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes.profile import profile_ask_instruction
from app.graph.nodes.quiz_bridge import build_quiz_shape_prompt
from app.graph.prompts.runtime.quiz import QUIZ_AGENT_SYSTEM
from app.graph.window import CONTEXT_WINDOW_MESSAGES, select_window


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
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع وكيل الاختبارات: يغلق على نموذج مربوط بأدوات الاختبارات فقط."""

    def _quiz_agent(state: ChatState) -> dict[str, list[BaseMessage]]:
        request = state.get("quiz_request")
        topic = request.topic if request and request.topic else ""
        plan = _coerce_plan(state.get("plan_draft"))
        shape = build_quiz_shape_prompt(request, plan)
        messages = list(state["messages"])
        last_text = message_text(messages[-1].content) if messages else ""
        history = select_window(messages, CONTEXT_WINDOW_MESSAGES)
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
            *history[-4:],
        ]
        reply = model.invoke(prompt)
        reply.name = "quiz_agent"
        return {"messages": [reply]}

    return _quiz_agent
