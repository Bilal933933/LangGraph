"""أساس نماذج SQLAlchemy بنمط 2.0 المعلن."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """أساس كل الجداول."""
