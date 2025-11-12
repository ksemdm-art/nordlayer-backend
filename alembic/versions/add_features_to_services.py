"""Add features column to services

Revision ID: add_features_to_services
Revises: remove_prices_from_services
Create Date: 2024-12-19 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_features_to_services'
down_revision = 'remove_prices_from_services'
branch_labels = None
depends_on = None


def upgrade():
    # Add features column to services table
    op.add_column('services', sa.Column('features', sa.JSON(), nullable=True))


def downgrade():
    # Remove features column
    op.drop_column('services', 'features')