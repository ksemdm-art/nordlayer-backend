"""remove_order_dependency_from_reviews

Revision ID: d1e2f3g4h5i6
Revises: cea74f257b37
Create Date: 2025-10-11 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3g4h5i6'
down_revision: Union[str, Sequence[str], None] = 'b2822d081009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove order dependency from reviews."""
    # Создаем новую таблицу без зависимости от заказов
    op.create_table('reviews_new',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=100), nullable=False),
        sa.Column('customer_email', sa.String(length=200), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_featured', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reviews_new_id'), 'reviews_new', ['id'], unique=False)
    
    # Копируем данные из старой таблицы
    op.execute("""
        INSERT INTO reviews_new (id, customer_name, customer_email, rating, title, content, images, is_approved, is_featured, created_at, updated_at)
        SELECT id, customer_name, customer_email, rating, title, content, images, is_approved, is_featured, created_at, updated_at
        FROM reviews
    """)
    
    # Удаляем старую таблицу
    op.drop_table('reviews')
    
    # Переименовываем новую таблицу
    op.rename_table('reviews_new', 'reviews')


def downgrade() -> None:
    """Restore order dependency to reviews."""
    # Создаем старую таблицу с зависимостью от заказов
    op.create_table('reviews_old',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('customer_name', sa.String(length=100), nullable=False),
        sa.Column('customer_email', sa.String(length=200), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_featured', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('order_id')
    )
    
    # Копируем данные (добавляем order_id = 0 для всех записей)
    op.execute("""
        INSERT INTO reviews_old (id, order_id, customer_name, customer_email, rating, title, content, images, is_approved, is_featured, created_at, updated_at)
        SELECT id, 0, customer_name, customer_email, rating, title, content, images, is_approved, is_featured, created_at, updated_at
        FROM reviews
    """)
    
    # Удаляем новую таблицу
    op.drop_table('reviews')
    
    # Переименовываем старую таблицу
    op.rename_table('reviews_old', 'reviews')