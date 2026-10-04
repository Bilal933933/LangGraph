"""اختبارات المصادقة (sqlite في الذاكرة، بلا Postgres حقيقي)."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import security
from app.auth.deps import get_db
from app.auth.models import RefreshSession, User  # noqa: F401 - تسجيل الجداول في Base
from app.auth.policy import normalize_email
from app.core.errors import AppError
from app.db.engine import dispose_engine
from app.db.models import Base
from app.main import create_app


@pytest.fixture()
def session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    sess = Session(engine)
    try:
        yield sess
    finally:
        sess.close()
        dispose_engine(engine)


def _override_app(sess: Session) -> TestClient:
    app = create_app()

    def _get_db():
        try:
            yield sess
            sess.commit()
        except Exception:
            sess.rollback()
            raise

    app.dependency_overrides[get_db] = _get_db
    return TestClient(app, raise_server_exceptions=False)


def test_register_login_me_refresh_logout(session: Session) -> None:
    client = _override_app(session)
    res = client.post("/auth/register", json={"email": "User@Example.com", "password": "secret123"})
    assert res.status_code == 201, res.text
    tokens = res.json()
    assert tokens["token_type"] == "bearer"

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "user@example.com"

    dup = client.post("/auth/register", json={"email": "user@example.com", "password": "secret123"})
    assert dup.status_code == 409

    bad = client.post("/auth/login", json={"email": "user@example.com", "password": "wrongpass1"})
    assert bad.status_code == 401

    login = client.post("/auth/login", json={"email": "user@example.com", "password": "secret123"})
    assert login.status_code == 200, login.text
    fresh = login.json()["refresh_token"]

    rotated = client.post("/auth/refresh", json={"refresh_token": fresh})
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["refresh_token"] != fresh

    reuse = client.post("/auth/refresh", json={"refresh_token": fresh})
    assert reuse.status_code == 401

    new_refresh = rotated.json()["refresh_token"]
    out = client.post("/auth/logout", json={"refresh_token": new_refresh})
    assert out.status_code == 204
    gone = client.post("/auth/refresh", json={"refresh_token": new_refresh})
    assert gone.status_code == 401


def test_invalid_token_rejected(session: Session) -> None:
    client = _override_app(session)
    res = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
    assert res.status_code == 401


def test_weak_password_and_bad_email_rejected(session: Session) -> None:
    client = _override_app(session)
    weak = client.post("/auth/register", json={"email": "a@b.com", "password": "short"})
    assert weak.status_code in (401, 422)
    bad_mail = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "secret123"}
    )
    assert bad_mail.status_code in (401, 422)


def test_password_never_stored_plain_and_normalized() -> None:
    hashed = security.hash_password("secret123")
    assert hashed != "secret123"
    assert security.verify_password("secret123", hashed)
    assert normalize_email("  USER@Example.COM ") == "user@example.com"
    with pytest.raises(AppError):
        normalize_email("not-an-email")
