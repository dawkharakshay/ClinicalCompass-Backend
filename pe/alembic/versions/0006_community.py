"""add community forum tables

Community posts/questions, threaded comments (with self-referential replies), and
per-post Yes/No polls. One poll vote per user per post; deleting a post cascades
to its comments and votes, and deleting a comment cascades to its replies.

Revision ID: 0006_community
Revises: 0005_discussions
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0006_community"
down_revision: Union[str, Sequence[str], None] = "0005_discussions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "community_posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("poll_question", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_posts_user_id", "community_posts", ["user_id"])

    op.create_table(
        "community_comments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("parent_comment_id", sa.Uuid(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["parent_comment_id"], ["community_comments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_community_comments_post_id", "community_comments", ["post_id"])
    op.create_index("ix_community_comments_user_id", "community_comments", ["user_id"])
    op.create_index(
        "ix_community_comments_parent_comment_id",
        "community_comments",
        ["parent_comment_id"],
    )

    op.create_table(
        "community_poll_votes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("vote", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["community_posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "user_id", name="uq_community_poll_votes_post_user"),
    )
    op.create_index(
        "ix_community_poll_votes_post_id", "community_poll_votes", ["post_id"]
    )
    op.create_index(
        "ix_community_poll_votes_user_id", "community_poll_votes", ["user_id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_community_poll_votes_user_id", table_name="community_poll_votes")
    op.drop_index("ix_community_poll_votes_post_id", table_name="community_poll_votes")
    op.drop_table("community_poll_votes")

    op.drop_index(
        "ix_community_comments_parent_comment_id", table_name="community_comments"
    )
    op.drop_index("ix_community_comments_user_id", table_name="community_comments")
    op.drop_index("ix_community_comments_post_id", table_name="community_comments")
    op.drop_table("community_comments")

    op.drop_index("ix_community_posts_user_id", table_name="community_posts")
    op.drop_table("community_posts")
