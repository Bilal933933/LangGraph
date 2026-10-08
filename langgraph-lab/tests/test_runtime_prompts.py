"""اختبارات ثابتة لبرومبتات التشغيل (بلا شبكة)."""

import app.graph.prompts as prompts
from app.graph.prompts.runtime.answer import ANSWER_SYSTEM
from app.graph.prompts.runtime.extract import EXTRACT_SYSTEM
from app.graph.prompts.runtime.knowledge_context import KNOWLEDGE_CONTEXT_SYSTEM
from app.graph.prompts.runtime.plan import PLAN_EXTRACT_SYSTEM
from app.graph.prompts.runtime.profile_ask import PROFILE_QUESTIONS, build_profile_ask
from app.graph.prompts.runtime.quiz import QUIZ_AGENT_SYSTEM
from app.graph.prompts.runtime.worksheet import WORKSHEET_EXTRACT_SYSTEM

_SYSTEM_NAMES = [
    "ANSWER_SYSTEM",
    "GREETING_SYSTEM",
    "PARSER_SYSTEM",
    "EXTRACT_SYSTEM",
    "PROFILE_SYSTEM",
    "PROFILE_INFO_SYSTEM",
    "PLAN_EXTRACT_SYSTEM",
    "QUIZ_AGENT_SYSTEM",
    "QUIZ_SHAPE_SYSTEM",
    "WORKSHEET_EXTRACT_SYSTEM",
    "WORKSHEET_SHAPE_SYSTEM",
]


def test_all_systems_exported_and_nonempty() -> None:
    for name in _SYSTEM_NAMES:
        text = getattr(prompts, name)
        assert isinstance(text, str) and text.strip(), name


def test_answer_system_sets_persona_and_limits() -> None:
    assert "مساعد المعلم" in ANSWER_SYSTEM
    assert "العربية" in ANSWER_SYSTEM
    assert "لا تخترع" in ANSWER_SYSTEM


def test_quiz_agent_constrains_quality() -> None:
    assert "مستقلة" in QUIZ_AGENT_SYSTEM
    assert "واحدة" in QUIZ_AGENT_SYSTEM
    assert "بلا مقدمات" in QUIZ_AGENT_SYSTEM


def test_profile_ask_builder_keeps_question_verbatim() -> None:
    text = build_profile_ask(PROFILE_QUESTIONS["subject"])
    assert "ما مادة تخصصك؟" in text
    assert "سطر مستقل" in text


def test_knowledge_context_guards_sources() -> None:
    assert "<source>" in KNOWLEDGE_CONTEXT_SYSTEM
    assert "للقراءة فقط" in KNOWLEDGE_CONTEXT_SYSTEM
    assert "لا تخترع" in KNOWLEDGE_CONTEXT_SYSTEM


def test_extractors_document_examples() -> None:
    assert "أمثلة:" in EXTRACT_SYSTEM
    assert "أمثلة:" in WORKSHEET_EXTRACT_SYSTEM
    assert "مثال:" in PLAN_EXTRACT_SYSTEM

