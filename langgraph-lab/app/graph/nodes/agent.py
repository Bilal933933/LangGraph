"""عقدة الوكيل (Agent = نموذج بأدوات يقرر وينفذ)."""

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from app.domain.ports import ChatModelPort
from app.domain.state import ChatState
from app.graph.content import message_text

AGENT_SYSTEM = """أنت مولد اختبارات لمساعد المعلم. عندك أداة fetch_lesson لجلب محتوى الدرس.
استدعها أولا بموضوع الطلب، ثم ولد الاختبار من المحتوى المرجع. الردود بالعربية."""


def make_agent_node(
    model: ChatModelPort,
) -> Callable[[ChatState], dict[str, list[BaseMessage]]]:
    """مصنع الوكيل: يغلق على نموذج مربوط بالأدوات."""

    def _agent(state: ChatState) -> dict[str, list[BaseMessage]]:
        request = state.get("quiz_request")
        topic = request.topic if request and request.topic else ""
        last_text = message_text(state["messages"][-1].content) if state["messages"] else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=AGENT_SYSTEM),
            HumanMessage(content=f"ولد اختبارا عن: {topic or last_text}"),
            *list(state["messages"][-4:]),
        ]
        reply = model.invoke(prompt)
        reply.name = "agent"
        return {"messages": [reply]}

    return _agent
