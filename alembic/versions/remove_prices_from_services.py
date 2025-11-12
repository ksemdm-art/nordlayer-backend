"""Remove prices and technical parameters from services

Revision ID: remove_prices_from_services
Revises: add_order_contact_fields
Create Date: 2024-12-19 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_prices_from_services'
down_revision = 'add_order_contact_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Remove price-related columns from services table
    op.drop_column('services', 'base_price')
    op.drop_column('services', 'price_factors')


def downgrade():
    # Add back price-related columns
    op.add_column('services', sa.Column('base_price', sa.Numeric(10, 2), nullable=True))
    op.add_column('services', sa.Column('price_factors', sa.JSON(), nullable=True))