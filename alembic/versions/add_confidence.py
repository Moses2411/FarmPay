"""add confidence to scan_results

Revision ID: add_confidence
Revises: add_notifications
Create Date: 2026-05-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'add_confidence'
down_revision: Union[str, None] = 'add_notifications'
branch: Union[str, None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('scan_results', sa.Column('confidence', sa.Float(), nullable=True, server_default='0.0'))


def downgrade() -> None:
    op.drop_column('scan_results', 'confidence')