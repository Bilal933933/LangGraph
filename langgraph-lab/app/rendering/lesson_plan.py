"""قالب خطة الدرس (عرض فقط)."""

from app.domain.models import LessonPlan


def render_lesson_plan(plan: LessonPlan, sources_block: str | None = None) -> str:
    """خطة محققة + مصادر ← نص نهائي بأقسام ثابتة."""
    lines = [
        f"تحضير درس: {plan.topic} ({plan.grade_level}) — {plan.minutes} دقيقة",
        "",
        f"الأهداف:\n{plan.objectives}",
        f"التمهيد:\n{plan.intro}",
        f"الشرح:\n{plan.steps}",
        f"الأنشطة:\n{plan.activities}",
        f"التقويم:\n{plan.assessment}",
    ]
    text = "\n\n".join(lines)
    if sources_block is not None and sources_block.strip():
        text = f"{text}\n\n---\n{sources_block.strip()}"
    return text
