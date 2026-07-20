"""switch password reset from link tokens to OTP codes

Repurpose ``password_reset_tokens`` for the OTP-based forgot-password flow:
- ``token_hash`` now stores a bcrypt hash of the numeric OTP (no longer a unique
  SHA-256 of an opaque link token), so its unique index is dropped.
- ``attempts`` caps how many times a code may be guessed before it is burned.
- ``used`` is gone: a code is deleted on consume/expiry rather than flagged.

Revision ID: 0004_password_reset_otp
Revises: 0003_feedback
Create Date: 2026-07-20 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_password_reset_otp"
down_revision: Union[str, Sequence[str], None] = "0003_feedback"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Any in-flight link tokens are meaningless under the new flow — clear them.
    op.execute("DELETE FROM password_reset_tokens")

    op.add_column(
        "password_reset_tokens",
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.drop_column("password_reset_tokens", "used")

    # token_hash is now a salted bcrypt hash, looked up by user_id — not unique.
    op.drop_index(
        "ix_password_reset_tokens_token_hash", table_name="password_reset_tokens"
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DELETE FROM password_reset_tokens")

    op.drop_index(
        "ix_password_reset_tokens_token_hash", table_name="password_reset_tokens"
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )

    op.add_column(
        "password_reset_tokens",
        sa.Column("used", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.drop_column("password_reset_tokens", "attempts")
