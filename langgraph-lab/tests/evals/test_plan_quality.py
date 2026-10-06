"""جودة الخطة حتميًا: خطة كاملة تنجح وناقصة تفشل."""

from app.domain.models import LessonPlan
from app.evals.plan_checks import evaluate_plan_render
from app.graph.prompts.responses.lesson_plan import render_lesson_plan


def _full_plan() -> LessonPlan:
    return LessonPlan(
        topic="الكسور",
        grade_level="الصف الرابع",
        minutes=45,
        objectives="أن يتعرف الطالب البسط والمقام.",
        intro="تمهيد بتقسيم تفاحة.",
        steps="شرح ثم أمثلة.",
        activities="ورقة عمل.",
        assessment="سؤال قصير.",
    )


def test_full_plan_render_passes() -> None:
    plan = _full_plan()
    result = evaluate_plan_render(plan, render_lesson_plan(plan))
    assert all(result.values()), result


def test_empty_sections_fail() -> None:
    plan = _full_plan()
    plan.objectives = ""
    plan.assessment = ""
    result = evaluate_plan_render(plan, render_lesson_plan(plan))
    assert result["non_empty_sections"] is False
    assert result["topic_present"] is True
