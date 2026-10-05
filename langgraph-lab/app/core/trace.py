"""التتبع (Trace = سجل مراحل رد النموذج في ملف محلي).

الخصوصية: الملف محلي فقط (مجلد logs متجاهل من git). تُسجل معطيات
المراحل (الأعداد والأزمنة) ونص الرد مقتطعا لأول 200 حرف فقط.
ممنوع تسجيل المفاتيح والأسرار — هذه الوحدة لا تستقبلها أصلا.
"""

import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from logging.handlers import RotatingFileHandler
from pathlib import Path

#: اسم اللوجر الموحد لكل العقد.
LOGGER_NAME = "langgraph-lab"
#: اسم ملف السجل داخل مجلد اللوجات.
LOG_FILENAME = "app.log"
#: أقصى طول لنص مسجل (يمنع تضخم الملف ويحد كشف المحتوى).
PREVIEW_CHARS = 200

_configured_for: Path | None = None


def setup_logging(log_dir: str | Path = "logs", level: str = "INFO") -> Path:
    """تهيئة مرة واحدة: ملف دوّار + كونسول. مجلد السجل ← مسار app.log.

    تكرار الاستدعاء لنفس المجلد لا يضيف معالجات مكررة.
    """
    global _configured_for
    target = Path(log_dir)
    target.mkdir(parents=True, exist_ok=True)
    log_file = target / LOG_FILENAME
    if _configured_for == log_file.resolve():
        return log_file
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level.upper())
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    _configured_for = log_file.resolve()
    return log_file


def get_logger(name: str = LOGGER_NAME) -> logging.Logger:
    """لوجر موحد: الاسم الافتراضي ← لوجر المشروع."""
    return logging.getLogger(name)


def preview(text: object) -> str:
    """نص للسجل: أول PREVIEW_CHARS حرفا فقط، بلا أسطر جديدة."""
    return " ".join(str(text).split())[:PREVIEW_CHARS]


@contextmanager
def stage(logger: logging.Logger, stage_name: str, **fields: object) -> Iterator[None]:
    """سياق مرحلة: سطر بداية ← تنفيذ ← سطر نهاية مع latency_ms."""
    extra = " ".join(f"{key}={value}" for key, value in fields.items())
    logger.info("stage=%s event=start %s", stage_name, extra)
    started = time.perf_counter()
    try:
        yield
    finally:
        latency_ms = (time.perf_counter() - started) * 1000
        logger.info("stage=%s event=end latency_ms=%.1f %s", stage_name, latency_ms, extra)
