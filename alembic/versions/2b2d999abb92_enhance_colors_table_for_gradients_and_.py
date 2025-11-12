"""enhance_colors_table_for_gradients_and_metallics

Revision ID: 2b2d999abb92
Revises: ce0bc997748f
Create Date: 2025-10-09 22:51:02.323033

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b2d999abb92'
down_revision: Union[str, Sequence[str], None] = 'ce0bc997748f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    
    # Create new table with enhanced structure
    op.create_table('colors_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('solid', 'gradient', 'metallic', name='colortype'), nullable=False, server_default='solid'),
        sa.Column('hex_code', sa.String(length=7), nullable=True),
        sa.Column('gradient_colors', sa.JSON(), nullable=True),
        sa.Column('gradient_direction', sa.String(length=20), nullable=True),
        sa.Column('metallic_base', sa.String(length=7), nullable=True),
        sa.Column('metallic_intensity', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('price_modifier', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO colors_new (id, name, type, hex_code, is_active, sort_order, price_modifier, created_at, updated_at)
        SELECT id, name, 'solid', hex_code, is_active, sort_order, 1.0, created_at, updated_at
        FROM colors
    """)
    
    # Drop old table and rename new table
    op.drop_table('colors')
    op.rename_table('colors_new', 'colors')
    
    # Recreate indexes
    op.create_index(op.f('ix_colors_id'), 'colors', ['id'], unique=False)
    op.create_index(op.f('ix_colors_name'), 'colors', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Recreate original table structure
    op.create_table('colors_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('hex_code', sa.String(length=7), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy data back (only solid colors with hex_code)
    op.execute("""
        INSERT INTO colors_old (id, name, hex_code, is_active, sort_order, created_at, updated_at)
        SELECT id, name, hex_code, is_active, sort_order, created_at, updated_at
        FROM colors
        WHERE type = 'solid' AND hex_code IS NOT NULL
    """)
    
    # Drop enhanced table and rename old table
    op.drop_table('colors')
    op.rename_table('colors_old', 'colors')
    
    # Recreate indexes
    op.create_index(op.f('ix_colors_id'), 'colors', ['id'], unique=False)
    op.create_index(op.f('ix_colors_name'), 'colors', ['name'], unique=False)
