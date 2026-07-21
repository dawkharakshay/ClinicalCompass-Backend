"""add discussions.created_by (author)

Records which user authored a discussion. Nullable so pre-existing rows (and
admin-seeded ones) stay valid; ON DELETE SET NULL keeps the discussion when the
author's account is removed.

Revision ID: 0009_discussion_created_by
Revises: 0008_drop_community
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0009_discussion_created_by"
down_revision: Union[str, Sequence[str], None] = "0008_drop_community"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "discussions", sa.Column("created_by", sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        "fk_discussions_created_by_users",
        "discussions",
        "users",
        ["created_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_discussions_created_by", "discussions", ["created_by"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_discussions_created_by", table_name="discussions")
    op.drop_constraint(
        "fk_discussions_created_by_users", "discussions", type_="foreignkey"
    )
    op.drop_column("discussions", "created_by")
