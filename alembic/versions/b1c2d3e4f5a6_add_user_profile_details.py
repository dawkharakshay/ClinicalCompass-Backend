"""add user medical_speciality and current_institution

Revision ID: b1c2d3e4f5a6
Revises: aeebae327c19
Create Date: 2026-06-16 16:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'aeebae327c19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('medical_speciality', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('current_institution', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'current_institution')
    op.drop_column('users', 'medical_speciality')
