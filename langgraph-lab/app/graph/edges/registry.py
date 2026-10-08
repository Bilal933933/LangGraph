"""سجل الحواف (Routes Registry = قائمة موجهات الرسم للتوسع).

القاعدة: أي مسار جديد = دالة توجيه في `edges/<feature>.py`
+ سطر تسجيل واحد هنا فقط. `builder.py` يلف على السجل ولا يتعدل.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from langgraph.types import Send

from app.domain.state import ChatState
from app.graph.edges.extract import route_after_extract
from app.graph.edges.loop import route_after_quiz_agent
from app.graph.edges.plan import route_after_plan_extract
from app.graph.edges.plan.worksheet import route_after_worksheet_extract
from app.graph.edges.profile import route_after_profile_extract
from app.graph.edges.request import route_by_request
from app.graph.nodes.plan import plan_dispatch


@dataclass(frozen=True)
class ConditionalRoute:
    """موجه مشروط واحد: المصدر + دالة القرار + الأهداف."""

    source: str
    router: Callable[[ChatState], str]
    targets: Mapping[str, str]


@dataclass(frozen=True)
class StaticEdge:
    """حافة ثابتة: من ← إلى دائما."""

    source: str
    target: str


@dataclass(frozen=True)
class SendRoute:
    """موجه Send: المصدر + دالة التوزيع المتوازي."""

    source: str
    router: Callable[[ChatState], list[Send]]


def core_send_routes() -> list[SendRoute]:
    """موجهات Send (fan-out المتوازي)."""
    return [SendRoute(source="plan_retrieve", router=plan_dispatch)]


def core_conditional_routes() -> list[ConditionalRoute]:
    """موجهات النواة الحالية، مرتبة حسب التنفيذ."""
    return [
        ConditionalRoute(
            source="validate_request",
            router=route_by_request,
            targets={
                "answer": "answer",
                "decline": "decline",
                "extract": "extract",
                "worksheet_extract": "worksheet_extract",
                "plan_extract": "plan_extract",
                "extract_profile": "extract_profile",
            },
        ),
        ConditionalRoute(
            source="worksheet_extract",
            router=route_after_worksheet_extract,
            targets={
                "worksheet_ask": "worksheet_ask",
                "worksheet_retrieve": "worksheet_retrieve",
            },
        ),
        ConditionalRoute(
            source="plan_extract",
            router=route_after_plan_extract,
            targets={
                "plan_ask": "plan_ask",
                "plan_retrieve": "plan_retrieve",
            },
        ),
        ConditionalRoute(
            source="extract",
            router=route_after_extract,
            targets={
                "ask_clarification": "ask_clarification",
                "confirm_ready": "confirm_ready",
            },
        ),
        ConditionalRoute(
            source="quiz_agent",
            router=route_after_quiz_agent,
            targets={"quiz_tools": "quiz_tools", "end": "end"},
        ),
        ConditionalRoute(
            source="extract_profile",
            router=route_after_profile_extract,
            targets={
                "save_profile": "save_profile",
                "ask_profile_name": "ask_profile_name",
            },
        ),
    ]


def core_static_edges() -> list[StaticEdge]:
    """حواف النواة الثابتة (END تعالج في builder).

    البداية تحمل الملف وتستنتجه وتطبقه بصمت قبل التصنيف،
    والنهايات عادية لأن السؤال تعليم في الموجه لا عقدة.
    """
    return [
        StaticEdge(source="__start__", target="load_profile"),
        StaticEdge(source="load_profile", target="extract_profile_info"),
        StaticEdge(source="extract_profile_info", target="apply_profile"),
        StaticEdge(source="apply_profile", target="parse_request"),
        StaticEdge(source="parse_request", target="validate_request"),
        StaticEdge(source="confirm_ready", target="quiz_agent"),
        StaticEdge(source="quiz_tools", target="quiz_agent"),
        StaticEdge(source="worksheet_retrieve", target="worksheet_write"),
        StaticEdge(source="worksheet_write", target="__end__"),
        StaticEdge(source="worksheet_ask", target="__end__"),
        StaticEdge(source="plan_section", target="plan_merge"),
        StaticEdge(source="plan_merge", target="__end__"),
        StaticEdge(source="plan_ask", target="__end__"),
        StaticEdge(source="answer", target="__end__"),
        StaticEdge(source="decline", target="__end__"),
        StaticEdge(source="ask_clarification", target="__end__"),
        StaticEdge(source="save_profile", target="__end__"),
        StaticEdge(source="ask_profile_name", target="__end__"),
    ]
