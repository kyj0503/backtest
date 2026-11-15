"""drop physical FK daily_prices.stock_id -> stocks.id

Revision ID: 7b2e9c4f1a30
Revises: d5c3763b29e6
Create Date: 2026-09-26 00:00:00.000000

A-10: 저장소에 남은 유일한 물리 FK(`daily_prices.stock_id → stocks.id
ON DELETE CASCADE`)를 제거한다. 이후 모든 테이블 간 참조는 논리 참조이며
무결성은 애플리케이션이 맡는다 (database/schema.sql의 daily_prices 주석 참고).

- CASCADE는 한 번도 발동한 적이 없다 — 코드에 `DELETE FROM stocks` 경로가 없다.
  반대로 stocks 삭제 기능이 생기면 코드에 드러나지 않은 채 일봉 전체가 지워진다.
- `(stock_id, date)` PK가 stock_id 조회 인덱스를 이미 제공하므로 FK를 떼도
  별도 인덱스 작업은 없다 (FK가 따로 만든 인덱스가 없음).
- 고아 행 점검/정리는 scripts/check_orphan_prices.py로 한다.

FK 이름은 하드코딩하지 않고 information_schema에서 찾는다. 초기 리비전
(622933e2fe2e)과 schema.sql 모두 이름 없이 FK를 선언해 MySQL이
`daily_prices_ibfk_1`로 자동 명명하지만, 운영 DB가 다른 경로로 만들어졌다면
이름이 다를 수 있다. 이미 FK가 없는 DB(이 변경 이후 schema.sql로 초기화한 DB)
에서도 실패하지 않는다.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b2e9c4f1a30'
down_revision: Union[str, Sequence[str], None] = 'd5c3763b29e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# downgrade가 되살릴 때 쓰는 이름 — MySQL이 자동 부여하던 이름과 같게 둔다
FK_NAME = 'daily_prices_ibfk_1'


def _daily_prices_fk_names(conn) -> list:
    rows = conn.execute(sa.text(
        """
        SELECT CONSTRAINT_NAME
        FROM information_schema.REFERENTIAL_CONSTRAINTS
        WHERE CONSTRAINT_SCHEMA = DATABASE()
          AND TABLE_NAME = 'daily_prices'
          AND REFERENCED_TABLE_NAME = 'stocks'
        """
    ))
    return [row[0] for row in rows]


def upgrade() -> None:
    """물리 FK 제거."""
    for name in _daily_prices_fk_names(op.get_bind()):
        op.drop_constraint(name, 'daily_prices', type_='foreignkey')


def downgrade() -> None:
    """물리 FK 복원 (이전과 같은 ON DELETE CASCADE).

    FK가 없던 동안 고아 행이 생겼다면 제약 생성이 실패한다 — 먼저
    scripts/check_orphan_prices.py --delete로 정리할 것.
    """
    if _daily_prices_fk_names(op.get_bind()):
        return
    op.create_foreign_key(
        FK_NAME, 'daily_prices', 'stocks', ['stock_id'], ['id'], ondelete='CASCADE'
    )
