"""مسجل واحد يلتقط كل الأخطاء ويحولها لرد موحد."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.errors import AppError, ErrorCode
from app.core.responses import fail


def register_error_handlers(app: FastAPI) -> None:
    """يربط المعالجات الثلاثة مرة واحدة من main."""

    async def _app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status,
            content=fail(exc.code.value, exc.message, exc.details),
        )

    async def _validation_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=fail(ErrorCode.VALIDATION_FAILED.value, "بيانات الطلب غير صالحة."),
        )

    async def _fallback_handler(_request: Request, _exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=fail(ErrorCode.INTERNAL.value, "خطأ داخلي غير متوقع."),
        )

    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _fallback_handler)
