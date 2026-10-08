"""برومتات أثناء الرد (ترسل للنموذج)."""

from app.graph.prompts.runtime.classify import CLASSIFY_SYSTEM
from app.graph.prompts.runtime.extract import EXTRACT_SYSTEM
from app.graph.prompts.runtime.greeting import GREETING_SYSTEM
from app.graph.prompts.runtime.plan import (
    PLAN_EXTRACT_SYSTEM,
    PLAN_REPAIR_SYSTEM,
    PLAN_SECTION_SYSTEMS,
)
from app.graph.prompts.runtime.profile import PROFILE_INFO_SYSTEM, PROFILE_SYSTEM
from app.graph.prompts.runtime.quiz import QUIZ_AGENT_SYSTEM
from app.graph.prompts.runtime.quiz_shape import QUIZ_SHAPE_SYSTEM
from app.graph.prompts.runtime.request import PARSER_SYSTEM
from app.graph.prompts.runtime.worksheet import WORKSHEET_EXTRACT_SYSTEM, WORKSHEET_SHAPE_SYSTEM

__all__ = [
    "CLASSIFY_SYSTEM",
    "GREETING_SYSTEM",
    "PARSER_SYSTEM",
    "EXTRACT_SYSTEM",
    "PROFILE_SYSTEM",
    "PROFILE_INFO_SYSTEM",
    "PLAN_EXTRACT_SYSTEM",
    "PLAN_SECTION_SYSTEMS",
    "PLAN_REPAIR_SYSTEM",
    "QUIZ_AGENT_SYSTEM",
    "QUIZ_SHAPE_SYSTEM",
    "WORKSHEET_EXTRACT_SYSTEM",
    "WORKSHEET_SHAPE_SYSTEM",
]
