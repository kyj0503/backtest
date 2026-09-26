"""
daily_prices 고아 행 점검/정리 스크립트

daily_prices.stock_id는 물리 FK 없이 stocks.id를 가리키는 논리 참조다
(A-10, database/schema.sql 참고). 읽기 경로는 항상 ticker → stocks.id →
daily_prices이므로, 부모 stocks 행이 없는 일봉은 영원히 조회되지 않고 디스크만
차지한다. 이 스크립트로 그런 행이 있는지 확인하고 필요하면 지운다.

실행 방법:
    docker exec backtest-be-fast-dev python scripts/check_orphan_prices.py

옵션:
    --delete: 고아 행을 실제로 삭제 (기본은 점검만 하고 아무것도 바꾸지 않음)

종료 코드:
    0 — 고아 행 없음, 또는 --delete로 정리 완료
    1 — 점검 모드에서 고아 행 발견 (cron/모니터링에서 알림 조건으로 쓸 수 있음)

작성일: 2026-09-26
"""

import argparse
import logging
import os
import sys

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import text

from app.services.database.connection_manager import DatabaseConnectionManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

ORPHAN_SUMMARY_SQL = text(
    """
    SELECT dp.stock_id, COUNT(*) AS row_count, MIN(dp.date) AS first_date, MAX(dp.date) AS last_date
    FROM daily_prices dp
    LEFT JOIN stocks s ON s.id = dp.stock_id
    WHERE s.id IS NULL
    GROUP BY dp.stock_id
    ORDER BY dp.stock_id
    """
)

# 점검과 삭제 사이에 새 stocks 행이 생길 수 있으므로 id 목록이 아니라 같은 조건으로 지운다
DELETE_ORPHANS_SQL = text(
    """
    DELETE dp FROM daily_prices dp
    LEFT JOIN stocks s ON s.id = dp.stock_id
    WHERE s.id IS NULL
    """
)


def check_orphan_prices(delete: bool = False) -> int:
    """고아 일봉 행 수를 반환한다. delete=True면 같은 트랜잭션에서 지운다."""
    engine = DatabaseConnectionManager.get_engine()

    with engine.begin() as conn:
        orphans = conn.execute(ORPHAN_SUMMARY_SQL).fetchall()
        total = sum(row.row_count for row in orphans)

        if not orphans:
            logger.info("고아 행 없음: 모든 daily_prices 행이 stocks를 참조합니다.")
            return 0

        for row in orphans:
            logger.warning(
                f"stock_id={row.stock_id}: {row.row_count}행 ({row.first_date} ~ {row.last_date})"
            )
        logger.warning(f"고아 행 합계: {len(orphans)}개 stock_id, {total}행")

        if delete:
            deleted = conn.execute(DELETE_ORPHANS_SQL).rowcount
            logger.info(f"고아 행 {deleted}행 삭제 완료")

    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="daily_prices 고아 행 점검/정리")
    parser.add_argument('--delete', action='store_true', help="고아 행을 실제로 삭제")
    args = parser.parse_args()

    total = check_orphan_prices(delete=args.delete)
    return 1 if total and not args.delete else 0


if __name__ == "__main__":
    sys.exit(main())
