"""add Google/Apple OAuth identity to users

Adds oauth_provider + oauth_subject (with a unique pair constraint) and makes
password_hash nullable so OAuth-only accounts need no password.

Revision ID: 0002_oauth_identity
Revises: 0001_initial
Create Date: 2026-06-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_oauth_identity"
down_revision: Union[str, Sequence[str], None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "password_hash", existing_type=sa.String(length=255), nullable=True
        )
        batch.add_column(sa.Column("oauth_provider", sa.String(length=16), nullable=True))
        batch.add_column(sa.Column("oauth_subject", sa.String(length=255), nullable=True))
        batch.create_unique_constraint(
            "uq_users_oauth_identity", ["oauth_provider", "oauth_subject"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_oauth_identity", type_="unique")
        batch.drop_column("oauth_subject")
        batch.drop_column("oauth_provider")
        batch.alter_column(
            "password_hash", existing_type=sa.String(length=255), nullable=False
        )
