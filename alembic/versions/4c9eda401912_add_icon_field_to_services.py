"""Add icon field to services

Revision ID: 4c9eda401912
Revises: d1e2f3g4h5i6
Create Date: 2025-10-21 15:12:02.918545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c9eda401912'
down_revision: Union[str, Sequence[str], None] = 'd1e2f3g4h5i6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Only add the icon column to services table
    op.add_column('services', sa.Column('icon', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove the icon column from services table
    op.drop_column('services', 'icon')
