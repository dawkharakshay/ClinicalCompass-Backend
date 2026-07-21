"""add discussions and discussion_votes tables

Admin-authored discussion topics (an assessment result paired with a
complication) that app users vote yes/no on. One vote per user per discussion,
enforced by a unique constraint; re-voting updates the existing row.

Revision ID: 0005_discussions
Revises: 0004_password_reset_otp
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005_discussions"
down_revision: Union[str, Sequence[str], None] = "0004_password_reset_otp"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "discussions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("assessment_result", sa.Text(), nullable=False),
        sa.Column("complication", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "discussion_votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("discussion_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vote", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["discussion_id"], ["discussions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "discussion_id", "user_id", name="uq_discussion_votes_discussion_user"
        ),
    )
    op.create_index(
        "ix_discussion_votes_discussion_id", "discussion_votes", ["discussion_id"]
    )
    op.create_index("ix_discussion_votes_user_id", "discussion_votes", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_discussion_votes_user_id", table_name="discussion_votes")
    op.drop_index("ix_discussion_votes_discussion_id", table_name="discussion_votes")
    op.drop_table("discussion_votes")
    op.drop_table("discussions")
