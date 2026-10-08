"""سجل العقد (Registry = قائمة تجمع العقد للتوسع).

القاعدة: أي ميزة جديدة = ملف عقدة جديد + سطر تسجيل واحد هنا فقط.
`builder.py` لا يتعدل عند إضافة العقد، بل يلف على هذا السجل.
"""

from collections.abc import Callable
from typing import Any

from app.domain.ports import (
    ChatModelPort,
    KnowledgeSearchPort,
    StructuredOutputPort,
    TeacherDirectoryPort,
    TeacherProfilePort,
    TeacherProfileWriterPort,
)
from app.graph.nodes.answer import make_answer_node, make_decline_node
from app.graph.nodes.extract import (
    ask_clarification_node,
    confirm_ready_node,
    make_extract_node,
)
from app.graph.nodes.parse import make_parse_request_node, validate_request_node
from app.graph.nodes.plan import (
    make_plan_clarification_node,
    make_plan_extract_node,
    make_plan_merge_node,
    make_plan_retrieve_node,
    make_plan_section_node,
)
from app.graph.nodes.profile import (
    ask_profile_name_node,
    make_apply_profile_node,
    make_extract_profile_info_node,
    make_extract_profile_node,
    make_load_profile_node,
    make_save_profile_node,
)
from app.graph.nodes.quiz_agent import make_quiz_agent_node
from app.graph.nodes.worksheet import (
    make_worksheet_ask_node,
    make_worksheet_extract_node,
    make_worksheet_retrieve_node,
    make_worksheet_write_node,
)


def core_nodes(
    model: ChatModelPort,
    structured: StructuredOutputPort,
    bound_quiz_model: ChatModelPort,
    teacher_directory: TeacherDirectoryPort | None = None,
    profile_writer: TeacherProfileWriterPort | None = None,
    profile_store: TeacherProfilePort | None = None,
    knowledge: KnowledgeSearchPort | None = None,
) -> dict[str, Callable[..., Any]]:
    """عقد النواة: الاسم ← دالة العقدة الجاهزة.

    كل وكيل جديد = ملف `*_agent.py` + سطر هنا + حلقته في سجل الحواف.
    bound_quiz_model مربوط بأدوات الاختبارات فقط، لا بكل الأدوات.
    profile_writer كاتب الاسم للمسار الصريح، وprofile_store لقطة الملف
    للمسار الاستنتاجي (تحميل واستنتاج وتطبيق صامت كل دور، والسؤال
    تعليم في موجه النموذج لا رسالة نظام).
    """
    nodes: dict[str, Callable[..., Any]] = {
        "parse_request": make_parse_request_node(structured),
        "validate_request": validate_request_node,
        "answer": make_answer_node(model, knowledge),
        "decline": make_decline_node(),
        "extract": make_extract_node(structured),
        "ask_clarification": ask_clarification_node,
        "confirm_ready": confirm_ready_node,
        "quiz_agent": make_quiz_agent_node(bound_quiz_model, structured),
        "extract_profile": make_extract_profile_node(structured),
        "ask_profile_name": ask_profile_name_node,
        "save_profile": make_save_profile_node(profile_writer),
        "load_profile": make_load_profile_node(profile_store),
        "extract_profile_info": make_extract_profile_info_node(structured),
        "apply_profile": make_apply_profile_node(profile_store),
        "plan_extract": make_plan_extract_node(structured),
        "plan_retrieve": make_plan_retrieve_node(knowledge),
        "plan_section": make_plan_section_node(model),
        "plan_ask": make_plan_clarification_node(),
        "plan_merge": make_plan_merge_node(model),
        "worksheet_extract": make_worksheet_extract_node(structured),
        "worksheet_ask": make_worksheet_ask_node(),
        "worksheet_retrieve": make_worksheet_retrieve_node(knowledge),
        "worksheet_write": make_worksheet_write_node(model, structured=structured),
    }
    return nodes
