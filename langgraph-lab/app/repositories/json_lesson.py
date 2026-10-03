"""مستودع الدروس من ملف JSON محلي (للتعلم)."""

import json
from pathlib import Path


class JsonLessonRepository:
    """يقرأ الدروس مرة واحدة ويبحث بالتطابق التقريبي."""

    def __init__(self, data_file: Path) -> None:
        raw = json.loads(data_file.read_text(encoding="utf-8"))
        lessons = raw.get("lessons", []) if isinstance(raw, dict) else []
        self._by_topic: dict[str, str] = {
            str(item.get("topic", "")).strip(): str(item.get("content", ""))
            for item in lessons
            if isinstance(item, dict) and str(item.get("content", "")).strip()
        }

    def get(self, topic: str) -> str | None:
        needle = topic.strip()
        if needle in self._by_topic:
            return self._by_topic[needle]
        for known, content in self._by_topic.items():
            if needle in known or known in needle:
                return content
        return None
