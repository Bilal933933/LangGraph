"""رد موحد لكل المشروع: نجاح أو فشل بنفس الشكل."""

from typing import Any


def ok(data: Any) -> dict[str, Any]:
    """نجاح: {"success": true, "data": ..., "error": null}."""
    return {"success": True, "data": data, "error": None}


def fail(code: str, message: str, details: object = None) -> dict[str, Any]:
    """فشل: {"success": false, "data": null, "error": {...}}."""
    return {
        "success": False,
        "data": None,
        "error": {"code": code, "message": message, "details": details},
    }
