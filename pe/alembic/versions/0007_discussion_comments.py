"""add discussion_comments table

Flat comments on a discussion (no threaded replies). Deleting a discussion
cascades to its comments; a user may delete only their own.

Revision ID: 0007_discussion_comments
Revises: 0006_community
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0007_discussion_comments"
down_revision: Union[str, Sequence[str], None] = "0006_community"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "discussion_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("discussion_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["discussion_id"], ["discussions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_discussion_comments_discussion_id", "discussion_comments", ["discussion_id"]
    )
    op.create_index(
        "ix_discussion_comments_user_id", "discussion_comments", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_discussion_comments_user_id", table_name="discussion_comments")
    op.drop_index(
        "ix_discussion_comments_discussion_id", table_name="discussion_comments"
    )
    op.drop_table("discussion_comments")
