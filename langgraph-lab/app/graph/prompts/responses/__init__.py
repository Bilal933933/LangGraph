"""قوالب الرد النهائي (تنسيق للعرض فقط، لا ترسل للنموذج)."""

from app.graph.prompts.responses.general import render_general
from app.graph.prompts.responses.lesson_plan import render_lesson_plan
from app.graph.prompts.responses.quiz_paper import render_quiz_paper
from app.graph.prompts.responses.worksheet_paper import render_worksheet_paper

__all__ = ["render_general", "render_lesson_plan", "render_quiz_paper", "render_worksheet_paper"]
