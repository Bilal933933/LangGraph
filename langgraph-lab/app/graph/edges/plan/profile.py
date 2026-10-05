"""موجه استيضاح بيانات المعلم (اسم معلق ← حفظ، وإلا ← سؤال)."""

from typing import Literal

from app.domain.state import ChatState

ProfileExtractTarget = Literal["save_profile", "ask_profile_name"]


def route_after_profile_extract(state: ChatState) -> ProfileExtractTarget:
    """اسم معلق موجود ← حفظ، وإلا ← سؤال عن الاسم."""
    pending = (state.get("pending_profile_name") or "").strip()
    if pending:
        return "save_profile"
    return "ask_profile_name"
