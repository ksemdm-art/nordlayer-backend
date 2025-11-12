"""Add new contact and delivery fields to orders

Revision ID: add_order_contact_fields
Revises: ff4e673016a2
Create Date: 2024-12-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_order_contact_fields'
down_revision = 'ff4e673016a2'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to orders table
    op.add_column('orders', sa.Column('customer_email', sa.String(200), nullable=True))
    op.add_column('orders', sa.Column('customer_phone', sa.String(50), nullable=True))
    op.add_column('orders', sa.Column('alternative_contact', sa.String(200), nullable=True))
    op.add_column('orders', sa.Column('delivery_needed', sa.String(10), nullable=True))
    op.add_column('orders', sa.Column('delivery_details', sa.Text(), nullable=True))
    
    # Migrate existing data: copy customer_contact to customer_email if it looks like email
    op.execute("""
        UPDATE orders 
        SET customer_email = customer_contact 
        WHERE customer_contact LIKE '%@%'
    """)


def downgrade():
    # Remove new columns
    op.drop_column('orders', 'delivery_details')
    op.drop_column('orders', 'delivery_needed')
    op.drop_column('orders', 'alternative_contact')
    op.drop_column('orders', 'customer_phone')
    op.drop_column('orders', 'customer_email')