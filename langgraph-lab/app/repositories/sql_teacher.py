"""دليل وملف المعلمين من SQL (جلسات قصيرة لكل عملية)."""

from sqlalchemy.orm import Session

from app.core.errors import AppError, ErrorCode
from app.db.engine import get_engine
from app.db.models.teacher import Teacher, TeacherGrade


class SqlTeacherDirectory:
    """قراءة الاسم للتحية + كتابة الاسم من المسار الحتمي فقط."""

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def get_name(self, teacher_id: int) -> str | None:
        """معرف ← اسم المعلم أو None."""
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                teacher = session.get(Teacher, teacher_id)
                if teacher is None:
                    return None
                name = (teacher.name or "").strip()
                return name or None
        finally:
            engine.dispose()

    def update_name(self, teacher_id: int, name: str) -> str:
        """يحفظ الاسم المنظف ← الاسم المحفوظ. فارغ أو مفقود ← خطأ."""
        cleaned = name.strip()[:100]
        if not cleaned:
            raise AppError(ErrorCode.VALIDATION_FAILED, "الاسم فارغ.", status=422)
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                teacher = session.get(Teacher, teacher_id)
                if teacher is None:
                    raise AppError(ErrorCode.NOT_FOUND, "المعلم غير موجود.", status=404)
                teacher.name = cleaned
                session.commit()
                return cleaned
        finally:
            engine.dispose()


class SqlTeacherProfile:
    """الملف الكامل بجلسات قصيرة: لقطة {name, subject, grades} + ترقيعها.

    grades قائمة تدمج اتحادا (بلا تكرار) لأن المعلم يدرس صفوفا متعددة.
    """

    def __init__(self, database_url: str) -> None:
        self._url = database_url

    def load_profile(self, teacher_id: int) -> dict[str, object]:
        """الهوية ← اللقطة (الغائب = "" أو []). مفقود ← خطأ 404."""
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                teacher = session.get(Teacher, teacher_id)
                if teacher is None:
                    raise AppError(ErrorCode.NOT_FOUND, "المعلم غير موجود.", status=404)
                grades = [g.grade for g in sorted(teacher.grades, key=lambda g: g.id or 0)]
                return {
                    "name": (teacher.name or "").strip(),
                    "subject": (teacher.subject or "").strip(),
                    "grades": grades,
                }
        finally:
            engine.dispose()

    def save_profile(self, teacher_id: int, patch: dict[str, object]) -> dict[str, object]:
        """يطبق القيم المنظفة غير الفارغة، والصفوف اتحادا ← اللقطة بعد الحفظ."""
        engine = get_engine(self._url)
        try:
            with Session(engine) as session:
                teacher = session.get(Teacher, teacher_id)
                if teacher is None:
                    raise AppError(ErrorCode.NOT_FOUND, "المعلم غير موجود.", status=404)
                name = patch.get("name")
                if isinstance(name, str) and name.strip():
                    teacher.name = name.strip()[:100]
                subject = patch.get("subject")
                if isinstance(subject, str) and subject.strip():
                    teacher.subject = subject.strip()[:100]
                grades = patch.get("grades")
                if isinstance(grades, list):
                    existing = {g.grade for g in teacher.grades}
                    for raw in grades[:20]:
                        cleaned = raw.strip()[:100] if isinstance(raw, str) else ""
                        if cleaned and cleaned not in existing:
                            session.add(TeacherGrade(teacher_id=teacher.id, grade=cleaned))
                            existing.add(cleaned)
                session.commit()
                grades = [g.grade for g in sorted(teacher.grades, key=lambda g: g.id or 0)]
                return {
                    "name": (teacher.name or "").strip(),
                    "subject": (teacher.subject or "").strip(),
                    "grades": grades,
                }
        finally:
            engine.dispose()
