"""add feedback table

Feedback on clinical recommendations (usefulness + clinical-judgment match +
optional comments). Potential-issue reports are stored flagged for review.

Revision ID: 0003_feedback
Revises: 0002_oauth_identity
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_feedback"
down_revision: Union[str, Sequence[str], None] = "0002_oauth_identity"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("usefulness", sa.String(length=20), nullable=False),
        sa.Column("clinical_judgment", sa.String(length=10), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("concern", sa.Text(), nullable=True),
        sa.Column("flagged", sa.Boolean(), nullable=False),
        sa.Column("subject_type", sa.String(length=50), nullable=True),
        sa.Column("subject_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])
    op.create_index("ix_feedback_flagged", "feedback", ["flagged"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_feedback_flagged", table_name="feedback")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_table("feedback")
