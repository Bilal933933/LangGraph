"""تهيئة مشتركة: تصفير محدد المعدل بين الاختبارات (IP واحد في TestClient)."""

import pytest

from app.core.limits import reset_rate_limits


@pytest.fixture(autouse=True)
def _reset_rate_limits_between_tests() -> None:
    reset_rate_limits()
    yield
    reset_rate_limits()
