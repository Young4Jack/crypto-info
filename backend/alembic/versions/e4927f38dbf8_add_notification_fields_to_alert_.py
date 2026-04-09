"""add notification fields to alert_histories

Revision ID: e4927f38dbf8
Revises: b7d5ed010e2a
Create Date: 2026-04-09 21:08:29.260935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4927f38dbf8'
down_revision: Union[str, None] = 'b7d5ed010e2a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 只添加新列，不做复杂的 ALTER
    op.add_column('alert_histories', sa.Column('notification_channel', sa.String(length=50), nullable=True))
    op.add_column('alert_histories', sa.Column('notification_group', sa.String(length=50), nullable=True))
    op.add_column('alert_histories', sa.Column('webhook_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('alert_histories', 'webhook_url')
    op.drop_column('alert_histories', 'notification_group')
    op.drop_column('alert_histories', 'notification_channel')