"""add_is_new_field_to_colors

Revision ID: ff4e673016a2
Revises: 2b2d999abb92
Create Date: 2025-10-09 23:07:08.250066

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff4e673016a2'
down_revision: Union[str, Sequence[str], None] = '2b2d999abb92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add is_new column to colors table
    op.add_column('colors', sa.Column('is_new', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove is_new column from colors table
    op.drop_column('colors', 'is_new')
