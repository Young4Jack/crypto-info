"""添加验证码开关设置

Revision ID: a1b2c3d4e5f6
Revises: f99034a55d90
Create Date: 2026-03-26 20:01:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f99034a55d90'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 添加验证码开关字段到系统设置表
    op.add_column('system_settings', sa.Column('enable_captcha', sa.Boolean(), default=False, comment='是否启用登录验证码'))

def downgrade() -> None:
    # 删除验证码开关字段
    op.drop_column('system_settings', 'enable_captcha')