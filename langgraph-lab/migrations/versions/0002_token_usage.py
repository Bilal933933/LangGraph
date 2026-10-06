"""token_usage: تجميع الرموز اليومي (001 بعد الأساس)."""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002_token_usage"
down_revision: str | None = "0001_baseline"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """ينشئ token_usage مع قيد الوحدة (subject, day)."""
    op.create_table(
        "token_usage",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("subject", sa.String(length=128), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject", "day", name="uq_token_usage_subject_day"),
    )
    op.create_index("ix_token_usage_subject", "token_usage", ["subject"])
    op.create_index("ix_token_usage_day", "token_usage", ["day"])


def downgrade() -> None:
    """يسقط token_usage."""
    op.drop_index("ix_token_usage_day", table_name="token_usage")
    op.drop_index("ix_token_usage_subject", table_name="token_usage")
    op.drop_table("token_usage")
