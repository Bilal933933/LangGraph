"""فحوصات هيكلية لورقة العمل المولدة (إشارات انحدار، لا إثبات جودة)."""

import re

#: أسطر مرقمة: "1)" أو "س1:" أو "تمرين 2." في بداية السطر.
_ITEM_MARK = re.compile(r"(?m)^\s*(?:تمرين\s*)?(?:س(?:ؤال)?\s*)?\d+\s*[.)\-:]")

#: مؤشرات مفتاح الإجابة.
_ANSWER_KEYS = ("الإجابات", "الإجابة", "مفتاح الإجابة", "نموذج الإجابة")

#: مؤشرات التمايز (دعم/إثراء).
_DIFF_KEYS = ("تمايز", "دعم", "إثراء", "المتعثرين", "المتقدمين")

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    """يطبع المسافات للمقارنة الحرفية."""
    return _WS.sub(" ", text).strip()


def mentions(text: str, phrase: str) -> bool:
    """عبارة ← حاضرة حرفيًا في النص."""
    cleaned = _norm(phrase)
    if not cleaned:
        return False
    return cleaned in _norm(text)


def count_numbered_items(text: str) -> int:
    """نص الورقة ← عدد التمارين المرقمة."""
    return len(_ITEM_MARK.findall(text))


def has_answer_key(text: str) -> bool:
    """نص الورقة ← هل يذكر مفتاح إجابة."""
    return any(key in text for key in _ANSWER_KEYS)


def has_differentiation(text: str) -> bool:
    """نص الورقة ← هل يذكر تمايزًا (دعم/إثراء)."""
    return any(key in text for key in _DIFF_KEYS)


def evaluate_worksheet_text(
    text: str, topic: str, grade: str, num_items: int
) -> dict[str, object]:
    """نص + متطلبات الطلب ← {topic_mentioned, grade_mentioned, item_count, has_answer_key, has_differentiation}."""
    return {
        "topic_mentioned": mentions(text, topic),
        "grade_mentioned": mentions(text, grade),
        "item_count": count_numbered_items(text),
        "num_items_required": num_items,
        "has_answer_key": has_answer_key(text),
        "has_differentiation": has_differentiation(text),
    }
