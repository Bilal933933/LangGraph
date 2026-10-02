"""تجميع الرسم (StateGraph + Edges خطية للمرحلة 1)."""

from typing import Any

from langchain_core.messages import BaseMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.domain.ports import ChatModelPort
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.nodes import classify_node, make_answer_node


class GeminiChatModel:
    """محول Gemini يحقق عقد ChatModelPort (SOLID: عكس الاعتماد)."""

    def __init__(self, api_key: str, model_name: str) -> None:
        self._llm = ChatGoogleGenerativeAI(model=model_name, google_api_key=api_key)

    def invoke(self, messages: list[BaseMessage]) -> str:
        result = self._llm.invoke(messages)
        return message_text(result.content)


def create_model(settings: Settings) -> ChatModelPort:
    """يبني محول Gemini أو يرفع خطأ واضحاً عند غياب المفتاح."""
    key = settings.google_api_key.get_secret_value().strip()
    if not key:
        raise AppError(
            ErrorCode.MISSING_API_KEY,
            "ضع GOOGLE_API_KEY في ملف .env (انسخ .env.example).",
            status=500,
        )
    return GeminiChatModel(api_key=key, model_name=settings.gemini_model)


def build_graph(model: ChatModelPort) -> Any:
    """START ← [classify] ← [answer] ← END (حافتان خطيتان).

    الحواف (Edges) هنا خطية. الحواف الشرطية في المرحلة 2.
    النوع Any لأن CompiledStateGraph من مكتبة خارجية بدون أنواع دقيقة.
    """
    graph: StateGraph[ChatState] = StateGraph(ChatState)
    graph.add_node("classify", classify_node)
    graph.add_node("answer", make_answer_node(model))  # type: ignore[arg-type]
    graph.add_edge(START, "classify")
    graph.add_edge("classify", "answer")
    graph.add_edge("answer", END)
    return graph.compile()
