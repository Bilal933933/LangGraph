"""فحوصات هيكلية لنص الاختبار المولد (إشارات انحدار، لا إثبات جودة)."""

import re

#: أسطر مرقمة: "1)" أو "س1:" أو "سؤال 2." في بداية السطر.
_QUESTION_MARK = re.compile(r"(?m)^\s*(?:س(?:ؤال)?\s*)?\d+\s*[.)\-:]")

#: مؤشرات مفتاح الإجابة.
_ANSWER_KEYS = ("الإجابات", "الإجابة", "مفتاح الإجابة", "نموذج الإجابة")

_WS = re.compile(r"\s+")

#: بادئات عربية ملصقة (للصف ← صف) تُجرّد للمقارنة فقط.
_PREFIXES = re.compile(r"^(?:لل|ل|ال)+")


def _norm(text: str) -> str:
    """يطبع المسافات للمقارنة الحرفية."""
    return _WS.sub(" ", text).strip()


def _bare(text: str) -> str:
    """يجرد بادئات ال/ل من كل كلمة (مقارنة متساهلة)."""
    return " ".join(_PREFIXES.sub("", word) for word in text.split())


def mentions(text: str, phrase: str) -> bool:
    """عبارة ← حاضرة حرفيًا أو بعد تجريد البادئات الملصقة."""
    cleaned = _norm(phrase)
    if not cleaned:
        return False
    body = _norm(text)
    if cleaned in body:
        return True
    return _bare(cleaned) in _bare(body)


def count_numbered_questions(text: str) -> int:
    """نص الاختبار ← عدد الأسئلة المرقمة."""
    return len(_QUESTION_MARK.findall(text))


def has_answer_key(text: str) -> bool:
    """نص الاختبار ← هل يذكر مفتاح إجابة."""
    return any(key in text for key in _ANSWER_KEYS)


def evaluate_quiz_text(
    text: str, topic: str, grade: str, num_questions: int
) -> dict[str, object]:
    """نص + متطلبات الطلب ← {topic_mentioned, grade_mentioned, question_count, has_answer_key}."""
    return {
        "topic_mentioned": mentions(text, topic),
        "grade_mentioned": mentions(text, grade),
        "question_count": count_numbered_questions(text),
        "num_questions_required": num_questions,
        "has_answer_key": has_answer_key(text),
    }
