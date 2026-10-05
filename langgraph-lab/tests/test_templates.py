"""اختبارات قوالب الرد: عامة + خطة درس (وهمي بلا Gemini)."""

from app.domain.models import LessonPlan
from app.graph.prompts.responses.general import render_general
from app.graph.prompts.responses.lesson_plan import render_lesson_plan


def test_general_renders_reply_and_sources() -> None:
    text = render_general("أهلاً بك!", "المصادر:\n1. الكتاب")
    assert "أهلاً بك!" in text
    assert "المصادر" in text


def test_general_without_sources() -> None:
    text = render_general("مرحباً", None)
    assert text == "مرحباً"


def test_lesson_plan_renders_all_sections() -> None:
    plan = LessonPlan(
        topic="الفاعل",
        grade_level="الثالث",
        minutes=45,
        objectives="الأهداف",
        intro="التمهيد",
        steps="الشرح",
        activities="الأنشطة",
        assessment="التقويم",
    )
    text = render_lesson_plan(plan, None)
    assert "تحضير درس: الفاعل" in text
    for section in ("الأهداف", "التمهيد", "الشرح", "الأنشطة", "التقويم"):
        assert section in text
