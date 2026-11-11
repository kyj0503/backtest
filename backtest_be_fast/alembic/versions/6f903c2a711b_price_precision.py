"""Preserve sub-cent adjusted prices and low-price assets.

Revision ID: 6f903c2a711b
Revises: 1f574a9ba22e
"""
from alembic import op
import sqlalchemy as sa

revision = '6f903c2a711b'
down_revision = '1f574a9ba22e'
branch_labels = None
depends_on = None


def upgrade():
    for name, comment in [('open', '시가'), ('high', '고가'), ('low', '저가'),
                          ('close', '종가'), ('adj_close', '수정 종가')]:
        op.alter_column('daily_prices', name, existing_type=sa.DECIMAL(19, 4),
                        type_=sa.DECIMAL(38, 18), existing_nullable=name == 'adj_close',
                        existing_comment=comment)


def downgrade():
    # Narrowing would irreversibly round valid prices. Restore a pre-upgrade
    # backup if a rollback is required; never silently discard precision.
    raise RuntimeError('Price precision downgrade requires an explicit backup restore.')
