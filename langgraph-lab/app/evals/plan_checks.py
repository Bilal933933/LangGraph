"""فحوصات عرض الخطة (الحقول والعناوين والأقسام غير الفارغة)."""

from app.domain.models import LessonPlan

#: عناوين الأقسام الخمسة الثابتة في العرض.
_SECTION_HEADERS = ("الأهداف:", "التمهيد:", "الشرح:", "الأنشطة:", "التقويم:")


def evaluate_plan_render(plan: LessonPlan, rendered: str) -> dict[str, object]:
    """خطة + عرضها ← حضور الموضوع/الصف/المدة والعناوين والأقسام."""
    sections = [plan.objectives, plan.intro, plan.steps, plan.activities, plan.assessment]
    return {
        "topic_present": plan.topic in rendered,
        "grade_present": plan.grade_level in rendered,
        "minutes_present": str(plan.minutes) in rendered,
        "headers_present": all(header in rendered for header in _SECTION_HEADERS),
        "non_empty_sections": all(section.strip() for section in sections),
    }
