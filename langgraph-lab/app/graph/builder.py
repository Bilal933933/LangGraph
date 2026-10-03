"""تجميع الرسم (مولد الاختبارات: تصنيف + استخراج + وكيل بأدوات)."""

from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.domain.ports import ChatModelPort, StructuredOutputPort
from app.domain.state import ChatState
from app.graph.adapters import GeminiChatModel, GeminiStructuredModel
from app.graph.edges import route_after_agent, route_after_extract, route_by_intent
from app.graph.nodes import (
    ask_clarification_node,
    confirm_ready_node,
    make_agent_node,
    make_answer_node,
    make_classify_node,
    make_decline_node,
    make_extract_node,
    make_greeting_node,
)


def _require_key(settings: Settings) -> str:
    key = settings.google_api_key.get_secret_value().strip()
    if not key:
        raise AppError(
            ErrorCode.MISSING_API_KEY,
            "ضع GOOGLE_API_KEY في ملف .env (انسخ .env.example).",
            status=500,
        )
    return key


def create_model(settings: Settings) -> ChatModelPort:
    """يبني محول Gemini النصي."""
    return GeminiChatModel(api_key=_require_key(settings), model_name=settings.gemini_model)


def create_structured(settings: Settings) -> StructuredOutputPort:
    """يبني محول المخرجات المهيكلة."""
    return GeminiStructuredModel(api_key=_require_key(settings), model_name=settings.gemini_model)


def build_graph(
    model: ChatModelPort, structured: StructuredOutputPort, tools: list[BaseTool]
) -> Any:
    """START ← [classify] ← شرطي → [greeting|answer|decline|extract] ← END.

    extract ← شرطي → [ask_clarification → END | confirm_ready → agent ⇄ tools].
    النوع Any لأن CompiledStateGraph من مكتبة خارجية بدون أنواع دقيقة.
    """
    bound = model.bind_tools(tools)
    graph: StateGraph[ChatState] = StateGraph(ChatState)
    graph.add_node("classify", make_classify_node(structured))  # type: ignore[call-overload]
    graph.add_node("greeting", make_greeting_node())  # type: ignore[call-overload]
    graph.add_node("answer", make_answer_node(model))  # type: ignore[call-overload]
    graph.add_node("decline", make_decline_node())  # type: ignore[call-overload]
    graph.add_node("extract", make_extract_node(structured))  # type: ignore[call-overload]
    graph.add_node("ask_clarification", ask_clarification_node)
    graph.add_node("confirm_ready", confirm_ready_node)
    graph.add_node("agent", make_agent_node(bound))  # type: ignore[arg-type]
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_by_intent,
        {
            "greeting": "greeting",
            "answer": "answer",
            "decline": "decline",
            "extract": "extract",
        },
    )
    graph.add_conditional_edges(
        "extract",
        route_after_extract,
        {
            "ask_clarification": "ask_clarification",
            "confirm_ready": "confirm_ready",
        },
    )
    graph.add_edge("confirm_ready", "agent")
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("greeting", END)
    graph.add_edge("answer", END)
    graph.add_edge("decline", END)
    graph.add_edge("ask_clarification", END)
    return graph.compile()
