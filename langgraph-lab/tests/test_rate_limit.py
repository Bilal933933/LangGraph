"""اختبارات محدد المعدل: نافذة منزلقة لكل مفتاح."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth.deps import get_db
from app.core.errors import AppError
from app.core.limits import check_rate, enforce_rate, reset_rate_limits
from app.db.engine import dispose_engine
from app.db.models import Base
from app.main import create_app


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset_rate_limits()


def test_allows_up_to_limit_then_blocks() -> None:
    assert check_rate("k1", limit=2, window=60.0, now=1000.0) == 0.0
    assert check_rate("k1", limit=2, window=60.0, now=1001.0) == 0.0
    assert check_rate("k1", limit=2, window=60.0, now=1002.0) > 0.0


def test_window_slides_old_hits_expire() -> None:
    check_rate("k2", limit=1, window=60.0, now=1000.0)
    assert check_rate("k2", limit=1, window=60.0, now=1000.0) > 0.0
    assert check_rate("k2", limit=1, window=60.0, now=1061.0) == 0.0


def test_keys_are_independent() -> None:
    check_rate("a", limit=1, window=60.0, now=1000.0)
    assert check_rate("b", limit=1, window=60.0, now=1000.0) == 0.0


def test_enforce_raises_429_with_retry_after() -> None:
    enforce_rate("k3", limit=1, window=60.0, now=1000.0)
    with pytest.raises(AppError) as exc:
        enforce_rate("k3", limit=1, window=60.0, now=1000.0)
    assert exc.value.status == 429
    assert exc.value.code.value == "RATE_LIMITED"


def test_register_rate_limited_over_http() -> None:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    app = create_app()

    def _get_db():  # type: ignore[no-untyped-def]
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app, raise_server_exceptions=False)
    try:
        codes: list[int] = []
        for i in range(11):
            res = client.post(
                "/auth/register",
                json={"email": f"rate{i}@example.com", "password": "secret123"},
            )
            codes.append(res.status_code)
        assert codes[-1] == 429
        assert res.json()["error"]["code"] == "RATE_LIMITED"
    finally:
        sess.close()
        dispose_engine(engine)
