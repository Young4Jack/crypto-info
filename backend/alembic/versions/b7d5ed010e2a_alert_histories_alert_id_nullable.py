"""alert_histories alert_id nullable

Revision ID: b7d5ed010e2a
Revises: c5814252a5ee
Create Date: 2026-04-09 21:02:59.257335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d5ed010e2a'
down_revision: Union[str, None] = 'c5814252a5ee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite 不支持 ALTER COLUMN DROP NOT NULL，使用表重建方式
    op.execute('''
        CREATE TABLE alert_histories_new (
            id INTEGER NOT NULL PRIMARY KEY,
            alert_id INTEGER,
            user_id INTEGER NOT NULL,
            crypto_id INTEGER NOT NULL,
            alert_type VARCHAR(20) NOT NULL,
            threshold_price FLOAT NOT NULL,
            trigger_price FLOAT NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'triggered',
            notification_sent TIMESTAMP,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    op.execute('''
        INSERT INTO alert_histories_new (id, alert_id, user_id, crypto_id, alert_type, threshold_price, trigger_price, status, notification_sent, created_at)
        SELECT id, alert_id, user_id, crypto_id, alert_type, threshold_price, trigger_price, status, notification_sent, created_at FROM alert_histories
    ''')
    op.execute('DROP TABLE alert_histories')
    op.execute('ALTER TABLE alert_histories_new RENAME TO alert_histories')


def downgrade() -> None:
    # 恢复原状（删除 alert_id 为 NULL 的记录）
    op.execute('DELETE FROM alert_histories WHERE alert_id IS NULL')
    op.alter_column('alert_histories', 'alert_id',
               existing_type=sa.INTEGER(),
               nullable=False)