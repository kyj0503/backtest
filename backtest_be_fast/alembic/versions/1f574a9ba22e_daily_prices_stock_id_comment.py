"""daily_prices.stock_id column comment: logical reference, no physical FK

Revision ID: 1f574a9ba22e
Revises: 7b2e9c4f1a30
Create Date: 2026-09-27 00:00:00.000000

A-11: schema.sql(initdb)과 `alembic upgrade head`의 최종 스키마를 COMMENT까지
일치시키면서, 초기 리비전(622933e2fe2e)이 남긴 `stock_id` 컬럼 COMMENT
'stocks 테이블의 ID (Foreign Key)'를 고친다. 물리 FK는 7b2e9c4f1a30에서
제거됐으므로 이 문구는 더 이상 사실이 아니다. 기존 리비전은 수정하지 않는다는
원칙에 따라 새 리비전으로 바꾸고, schema.sql도 같은 문구를 COMMENT로 쓴다.

- 컬럼 COMMENT 변경은 InnoDB에서 메타데이터만 바꾸는 작업이다. mysql:8.4에서
  `ALTER TABLE ... MODIFY stock_id int NOT NULL COMMENT '...', ALGORITHM=INSTANT`가
  허용되고 행 버전(INNODB_TABLES.TOTAL_ROW_VERSIONS)도 늘지 않음을 확인했다 —
  PK 컬럼이지만 daily_prices 재작성이 일어나지 않는다.
- schema.sql로 만든 기존 DB(dev/운영)는 이 컬럼에 COMMENT가 없었다. 이 리비전을
  적용하면 이 컬럼만 새 문구를 갖는다. 다른 컬럼의 COMMENT 차이(기존 DB에는
  없거나 이중 인코딩돼 있음)는 동작에 영향이 없어 이 리비전에서 다루지 않는다.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f574a9ba22e'
down_revision: Union[str, Sequence[str], None] = '7b2e9c4f1a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_COMMENT = 'stocks 테이블의 ID (Foreign Key)'
NEW_COMMENT = 'stocks.id 논리 참조 (물리 FK 없음)'


def upgrade() -> None:
    """stock_id COMMENT를 논리 참조로 갱신 (타입·NULL 여부는 그대로)."""
    op.alter_column(
        'daily_prices', 'stock_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_comment=OLD_COMMENT,
        comment=NEW_COMMENT,
    )


def downgrade() -> None:
    """초기 리비전의 COMMENT로 되돌린다."""
    op.alter_column(
        'daily_prices', 'stock_id',
        existing_type=sa.Integer(),
        existing_nullable=False,
        existing_comment=NEW_COMMENT,
        comment=OLD_COMMENT,
    )
