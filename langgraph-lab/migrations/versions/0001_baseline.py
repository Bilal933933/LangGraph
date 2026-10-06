"""baseline: لقطة المخطط الحالي (users/teachers/conversations/messages/quizzes/knowledge).

الترحيلات اللاحقة يجب أن تكون op.* صريحة، لا create_all جديدة.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

import app.auth.models as _auth_models  # noqa: F401 - تسجيل users في metadata
import app.db.models as _models  # noqa: F401 - تسجيل knowledge_chunks
from app.db.models.base import Base

revision: str = "0001_baseline"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """خط الأساس: ينشئ كل الجداول الحالية دفعة واحدة (آمن للتكرار)."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """يعكس الأساس: يسقط كل الجداول (لبيئات التطوير فقط)."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
