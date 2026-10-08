"""عقد الملف الشخصي (استخراج حتمي + حفظ حتمي، بلا أدوات).

النموذج يقترح الاسم فقط عبر مخرجات مهيكلة، والنظام هو من يكتب
في القاعدة بالهوية من الحالة (teacher_id)، لا من وسائط النموذج.
"""

from collections.abc import Callable

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.core.errors import AppError
from app.domain.models import ProfileInfo, ProfileName
from app.domain.ports import (
    StructuredOutputPort,
    TeacherProfilePort,
    TeacherProfileWriterPort,
)
from app.domain.state import ChatState
from app.graph.content import message_text
from app.graph.prompts import PROFILE_INFO_SYSTEM, PROFILE_SYSTEM
from app.graph.prompts.runtime.profile_ask import PROFILE_QUESTIONS, build_profile_ask


def make_extract_profile_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """يستخرج الاسم من آخر رسالة ← pending_profile_name (أو None)."""

    def _extract(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=PROFILE_SYSTEM),
            HumanMessage(content=last),
        ]
        try:
            result = structured.parse(prompt, ProfileName)
            name = (result.name or "").strip()
            return {"pending_profile_name": name or None}
        except Exception:
            return {"pending_profile_name": None}

    return _extract


def make_save_profile_node(
    writer: TeacherProfileWriterPort | None,
) -> Callable[[ChatState], dict[str, object]]:
    """يحفظ الاسم بالهوية من الحالة ← ترحيب طبيعي بلا كلام نظام."""

    def _save(state: ChatState) -> dict[str, object]:
        teacher_id = state.get("teacher_id")
        raw = state.get("pending_profile_name") or ""
        name = raw.strip()[:100]
        if not isinstance(teacher_id, int):
            text = "لا توجد هوية مسجلة، سجل الدخول أولا ثم أخبرني باسمك."
            return {
                "messages": [AIMessage(content=text)],
                "pending_profile_name": None,
            }
        if not name:
            text = "ما الاسم الذي تريد تسجيله؟"
            return {
                "messages": [AIMessage(content=text)],
                "pending_profile_name": None,
            }
        if writer is None:
            text = "خدمة الحفظ غير مهيأة الآن، حاول لاحقا."
            return {
                "messages": [AIMessage(content=text)],
                "pending_profile_name": None,
            }
        try:
            saved = writer.update_name(teacher_id, name)
        except AppError as exc:
            return {
                "messages": [AIMessage(content=str(exc))],
                "pending_profile_name": None,
            }
        text = f"أهلا بك يا {saved}!"
        return {
            "messages": [AIMessage(content=text)],
            "pending_profile_name": None,
        }

    return _save


def ask_profile_name_node(state: ChatState) -> dict[str, list[BaseMessage]]:
    """لا اسم مستخرج ← سؤال مباشر عن الاسم."""
    _ = state
    return {"messages": [AIMessage(content="ما الاسم الذي تريد تسجيله؟")]}


_PROFILE_FIELDS = ("name", "subject", "grades")


def _clean_str(value: object) -> str:
    return value.strip()[:100] if isinstance(value, str) else ""


def _clean_grades(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    seen: list[str] = []
    for raw in value[:20]:
        cleaned = _clean_str(raw)
        if cleaned and cleaned not in seen:
            seen.append(cleaned)
    return seen


def _is_filled(value: object) -> bool:
    if isinstance(value, list):
        return len(value) > 0
    return bool(_clean_str(value))


def make_load_profile_node(
    store: TeacherProfilePort | None,
) -> Callable[[ChatState], dict[str, object]]:
    """يحمل لقطة الملف كل دور ← profile_snapshot. بلا مخزن أو هوية ← صمت."""

    def _load(state: ChatState) -> dict[str, object]:
        teacher_id = state.get("teacher_id")
        if store is None or not isinstance(teacher_id, int):
            return {}
        try:
            snapshot = store.load_profile(teacher_id)
        except Exception:
            return {}
        return {"profile_snapshot": {k: snapshot.get(k, "") for k in _PROFILE_FIELDS}}

    return _load


def make_extract_profile_info_node(
    structured: StructuredOutputPort,
) -> Callable[[ChatState], dict[str, object]]:
    """يستنتج حقول الملف من آخر رسالة كل دور ← pending_profile (لا كتابة هنا)."""

    def _extract(state: ChatState) -> dict[str, object]:
        messages = state.get("messages", [])
        last = message_text(messages[-1].content) if messages else ""
        prompt: list[BaseMessage] = [
            SystemMessage(content=PROFILE_INFO_SYSTEM),
            HumanMessage(content=last),
        ]
        try:
            result = structured.parse(prompt, ProfileInfo)
        except Exception:
            return {"pending_profile": None}
        patch: dict[str, object] = {}
        if _clean_str(result.name):
            patch["name"] = _clean_str(result.name)
        if _clean_str(result.subject):
            patch["subject"] = _clean_str(result.subject)
        if _clean_grades(result.grades):
            patch["grades"] = _clean_grades(result.grades)
        return {"pending_profile": patch or None}

    return _extract


def missing_profile_fields(snapshot: dict[str, object]) -> list[str]:
    """اللقطة ← الحقول الفارغة فقط (الصفوف تكتمل بصف واحد على الأقل)."""
    return [field for field in _PROFILE_FIELDS if not _is_filled(snapshot.get(field))]


def profile_ask_instruction(snapshot: dict[str, object]) -> str | None:
    """اللقطة ← تعليم سؤال طبيعي للنموذج، أو None عند الاكتمال.

    سؤال واحد فقط (أول الناقص) وبصيغة عقد إخراج مثبتة آخر الرد،
    فلا رسالة نظام منفصلة أبدا ولا إخبار بأي حفظ.
    """
    missing = missing_profile_fields(snapshot)
    if not missing:
        return None
    return build_profile_ask(PROFILE_QUESTIONS[missing[0]])


def make_apply_profile_node(
    store: TeacherProfilePort | None,
) -> Callable[[ChatState], dict[str, object]]:
    """يطبق ترقيع الملف بصمت تام (بلا رسائل) ← لقطة محدثة.

    يعمل كل دور قبل التصنيف، فيرى النموذج بعده ملفا محدثا دائما.
    """

    def _apply(state: ChatState) -> dict[str, object]:
        teacher_id = state.get("teacher_id")
        if store is None or not isinstance(teacher_id, int):
            return {"pending_profile": None}
        try:
            stored = dict(state.get("profile_snapshot") or store.load_profile(teacher_id))
        except Exception:
            return {"pending_profile": None}
        pending = dict(state.get("pending_profile") or {})
        patch: dict[str, object] = {}
        for field in _PROFILE_FIELDS:
            if field == "grades":
                raw_known = stored.get("grades", [])
                known = (
                    {g for g in raw_known if isinstance(g, str)}
                    if isinstance(raw_known, list)
                    else set()
                )
                fresh = [g for g in _clean_grades(pending.get("grades")) if g not in known]
                if fresh:
                    patch[field] = fresh
            elif _clean_str(pending.get(field)) and not _is_filled(stored.get(field)):
                patch[field] = _clean_str(pending.get(field))
        if not patch:
            return {"profile_snapshot": stored, "pending_profile": None}
        try:
            updated = store.save_profile(teacher_id, patch)
        except Exception:
            return {"profile_snapshot": stored, "pending_profile": None}
        return {"profile_snapshot": updated, "pending_profile": None}

    return _apply
