"""initial rag schema

Revision ID: b395c64c04c3
Revises:
Create Date: 2026-08-16 22:51:56.816639

"""

from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = "b395c64c04c3"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
