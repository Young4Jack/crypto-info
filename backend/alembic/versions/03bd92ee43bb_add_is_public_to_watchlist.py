"""add_is_public_to_watchlist

Revision ID: 03bd92ee43bb
Revises: 249bba56d7a1
Create Date: 2026-04-03 08:01:11.596497

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '03bd92ee43bb'
down_revision: Union[str, None] = '249bba56d7a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('watchlist', sa.Column('is_public', sa.Boolean(), nullable=False, server_default='1'))


def downgrade() -> None:
    op.drop_column('watchlist', 'is_public')
