"""إثبات اتصال DB (بلا Postgres حقيقي: sqlite للنجاح، رابط ميت للفشل)."""

import pytest
from sqlalchemy import create_engine

from app.core.errors import AppError
from app.db.engine import check_connection, dispose_engine, get_engine


def test_get_engine_creates() -> None:
    engine = get_engine("sqlite:///:memory:")
    try:
        assert engine is not None
    finally:
        dispose_engine(engine)


def test_check_connection_ok() -> None:
    engine = create_engine("sqlite:///:memory:")
    try:
        check_connection(engine)  # لا يرمي = ناجح
    finally:
        engine.dispose()


def test_check_connection_failed_raises_arabic_error() -> None:
    engine = get_engine("postgresql+psycopg://bad:bad@localhost:1/bad?connect_timeout=1")
    try:
        with pytest.raises(AppError):
            check_connection(engine)
    finally:
        dispose_engine(engine)
