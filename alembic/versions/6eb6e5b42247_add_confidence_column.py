"""fix uuid columns type

Revision ID: 6eb6e5b42247
Revises: add_notifications
Create Date: 2026-05-11 14:41:05.382076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6eb6e5b42247'
down_revision: Union[str, Sequence[str], None] = 'add_notifications'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix UUID columns that may have been created as INTEGER/NUMERIC on deployment."""
    for table, columns in [
        ('dispute_images', ['id', 'dispute_id']),
        ('disputes', ['id', 'order_id', 'buyer_id', 'admin_id']),
        ('farmer_profiles', ['id', 'user_id']),
        ('notifications', ['id', 'user_id']),
        ('order_items', ['id', 'order_id', 'product_id']),
        ('orders', ['id', 'buyer_id', 'dispatch_rider_id']),
        ('payments', ['id', 'order_id']),
        ('product_images', ['id', 'product_id']),
        ('products', ['id', 'farmer_id']),
        ('reviews', ['id', 'product_id', 'buyer_id']),
        ('scan_results', ['id', 'image_id']),
        ('users', ['id']),
    ]:
        for col in columns:
            try:
                op.alter_column(table, col, type_=sa.UUID(), existing_type=sa.INTEGER(), server_default=None)
            except Exception:
                pass


def downgrade() -> None:
    """Downgrade - not typically needed."""
    pass