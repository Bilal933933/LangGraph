"""سجل العقد (Registry = قائمة تجمع العقد للتوسع).

القاعدة: أي ميزة جديدة = ملف عقدة جديد + سطر تسجيل واحد هنا فقط.
`builder.py` لا يتعدل عند إضافة العقد، بل يلف على هذا السجل.
"""

from collections.abc import Callable
from typing import Any

from app.domain.ports import (
    ChatModelPort,
    StructuredOutputPort,
    TeacherDirectoryPort,
    TeacherProfilePort,
    TeacherProfileWriterPort,
)
from app.graph.nodes.answer import make_answer_node, make_decline_node, make_greeting_node
from app.graph.nodes.classify import make_classify_node
from app.graph.nodes.extract import (
    ask_clarification_node,
    confirm_ready_node,
    make_extract_node,
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


def core_nodes(
    model: ChatModelPort,
    structured: StructuredOutputPort,
    bound_quiz_model: ChatModelPort,
    teacher_directory: TeacherDirectoryPort | None = None,
    profile_writer: TeacherProfileWriterPort | None = None,
    profile_store: TeacherProfilePort | None = None,
) -> dict[str, Callable[..., Any]]:
    """عقد النواة: الاسم ← دالة العقدة الجاهزة.

    كل وكيل جديد = ملف `*_agent.py` + سطر هنا + حلقته في سجل الحواف.
    bound_quiz_model مربوط بأدوات الاختبارات فقط، لا بكل الأدوات.
    profile_writer كاتب الاسم للمسار الصريح، وprofile_store لقطة الملف
    للمسار الاستنتاجي (تحميل واستنتاج وتطبيق صامت كل دور، والسؤال
    تعليم في موجه النموذج لا رسالة نظام).
    """
    nodes: dict[str, Callable[..., Any]] = {
        "classify": make_classify_node(structured),
        "greeting": make_greeting_node(teacher_directory),
        "answer": make_answer_node(model),
        "decline": make_decline_node(),
        "extract": make_extract_node(structured),
        "ask_clarification": ask_clarification_node,
        "confirm_ready": confirm_ready_node,
        "quiz_agent": make_quiz_agent_node(bound_quiz_model),
        "extract_profile": make_extract_profile_node(structured),
        "ask_profile_name": ask_profile_name_node,
        "save_profile": make_save_profile_node(profile_writer),
        "load_profile": make_load_profile_node(profile_store),
        "extract_profile_info": make_extract_profile_info_node(structured),
        "apply_profile": make_apply_profile_node(profile_store),
    }
    return nodes
