"""اختبارات ثابتة لجسر الاختبار (بلا شبكة)."""

from app.domain.models import LessonPlan, QuizRequest
from app.graph.nodes.quiz_bridge import build_quiz_shape_prompt, quiz_request_from_plan


def test_shape_mentions_topic_grade_count() -> None:
    req = QuizRequest(topic="QT", grade_level="QG", num_questions=7)
    shape = build_quiz_shape_prompt(req, None)
    assert "QT" in shape and "QG" in shape and "7" in shape


def test_shape_prefers_explicit_types() -> None:
    req = QuizRequest(topic="QT", question_types=["TT"])
    assert "TT" in build_quiz_shape_prompt(req, None)


def test_shape_falls_back_to_plan() -> None:
    plan = LessonPlan(topic="PT", grade_level="PG", minutes=45, objectives="PO")
    shape = build_quiz_shape_prompt(QuizRequest(), plan)
    assert "PT" in shape and "PO" in shape


def test_request_from_plan_clamps_count() -> None:
    plan = LessonPlan(topic="PT", grade_level="PG", minutes=45)
    assert quiz_request_from_plan(plan, 0).num_questions == 1
    assert quiz_request_from_plan(plan, 99).num_questions == 50
    req = quiz_request_from_plan(plan, 5)
    assert (req.topic, req.grade_level, req.num_questions) == ("PT", "PG", 5)

