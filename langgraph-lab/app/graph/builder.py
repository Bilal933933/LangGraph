"""تجميع الرسم (مولد الاختبارات: تصنيف + استخراج + وكيل بأدوات)."""

from typing import Any

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from app.core.config import Settings
from app.core.errors import AppError, ErrorCode
from app.domain.ports import (
    ChatModelPort,
    StructuredOutputPort,
    TeacherDirectoryPort,
    TeacherProfilePort,
    TeacherProfileWriterPort,
)
from app.domain.state import ChatState
from app.graph.adapters import GeminiChatModel, GeminiStructuredModel
from app.graph.edges.registry import core_conditional_routes, core_static_edges
from app.graph.nodes.registry import core_nodes


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
    model: ChatModelPort,
    structured: StructuredOutputPort,
    tools: list[BaseTool],
    checkpointer: Any | None = None,
    teacher_directory: TeacherDirectoryPort | None = None,
    profile_writer: TeacherProfileWriterPort | None = None,
    profile_store: TeacherProfilePort | None = None,
) -> Any:
    """START ← [load_profile → extract_profile_info → apply_profile → classify] ← شرطي → ....

    النهايات عادية ← END. سؤال الباقي تعليم في موجه النموذج (answer وquiz_agent)
    لا عقدة، واستخراج update_profile الصريح ما زال يعمل كما كان.

    extract ← شرطي → [ask_clarification → END | confirm_ready → quiz_agent ⇄ quiz_tools].
    extract_profile ← شرطي → [save_profile → END | ask_profile_name → END].
    كل وكيل له أدواته وحلقته الخاصة (quiz_agent ⇄ quiz_tools).
    النوع Any لأن CompiledStateGraph من مكتبة خارجية بدون أنواع دقيقة.
    checkpointer فارغ = بلا حفظ بين الطلبات (توافق خلفي للاختبارات).

    قاعدة التوسع: العقد والموجهات تأتي من السجلات
    (nodes/registry.py + edges/registry.py). وكيل جديد = ملف
    `*_agent.py` + أدواته + سطر في كل سجل، بدون تعديل هذه الدالة.
    """
    quiz_tools = list(tools)
    bound_quiz = model.bind_tools(quiz_tools)
    graph: StateGraph[ChatState] = StateGraph(ChatState)
    nodes = core_nodes(
        model, structured, bound_quiz, teacher_directory, profile_writer, profile_store
    )
    for name, node in nodes.items():
        graph.add_node(name, node)
    graph.add_node("quiz_tools", ToolNode(quiz_tools))
    for route in core_conditional_routes():
        targets = {k: (END if v == "end" else v) for k, v in route.targets.items()}
        graph.add_conditional_edges(route.source, route.router, targets)  # type: ignore[arg-type]
    for edge in core_static_edges():
        source = START if edge.source == "__start__" else edge.source
        target = END if edge.target == "__end__" else edge.target
        graph.add_edge(source, target)
    if checkpointer is None:
        return graph.compile()
    return graph.compile(checkpointer=checkpointer)
