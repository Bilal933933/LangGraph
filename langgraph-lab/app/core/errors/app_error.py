"""أخطاء النطاق الموحدة."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """رموز ثابتة بدل النصوص الحرة."""

    MISSING_API_KEY = "MISSING_API_KEY"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    LLM_FAILED = "LLM_FAILED"
    INTERNAL = "INTERNAL"


class AppError(Exception):
    """خطأ واحد يحمله أي مكان في المشروع ويلتقطه المعالج."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status: int = 500,
        details: object = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status
        self.details = details
