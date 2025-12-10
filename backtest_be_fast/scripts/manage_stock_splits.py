"""
주가 분할 메타데이터 정기 업데이트 스크립트

모든 종목의 분할 정보를 yfinance에서 조회하여 DB에 저장합니다.
이를 통해 백테스트 실행 시 API 호출을 최소화합니다.

실행 방법:
    docker exec backtest-be-fast-dev python scripts/update_split_metadata.py

옵션:
    --batch-size: 한 번에 처리할 종목 수 (기본: 50)
    --max-age-days: 업데이트 대상 기준 일수 (기본: 7일)
    --all: 모든 종목 강제 업데이트

예시:
    # 7일 이상 된 종목만 50개씩 업데이트
    docker exec backtest-be-fast-dev python scripts/update_split_metadata.py

    # 모든 종목 강제 업데이트 (100개씩)
    docker exec backtest-be-fast-dev python scripts/update_split_metadata.py --all --batch-size 100

작성일: 2025-11-29
"""

import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import datetime, timedelta
from sqlalchemy import text
from app.services.database.connection_manager import DatabaseConnectionManager
import yfinance as yf
import pandas as pd
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_split_metadata_batch(batch_size: int = 50, max_age_days: int = 7, force_all: bool = False):
    """
    분할 정보 배치 업데이트

    Args:
        batch_size: 한 번에 처리할 종목 수
        max_age_days: 이보다 오래된 데이터만 업데이트
        force_all: True면 모든 종목 강제 업데이트
    """
    engine = DatabaseConnectionManager.get_engine()
    conn = engine.connect()

    try:
        # 업데이트가 필요한 종목 조회
        if force_all:
            query = text("""
                SELECT ticker, last_split_date, splits_updated_at
                FROM stocks
                ORDER BY splits_updated_at ASC
                LIMIT :limit
            """)
            params = {"limit": batch_size}
        else:
            cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
            query = text("""
                SELECT ticker, last_split_date, splits_updated_at
                FROM stocks
                WHERE splits_updated_at IS NULL
                   OR splits_updated_at < :cutoff
                ORDER BY splits_updated_at ASC
                LIMIT :limit
            """)
            params = {"cutoff": cutoff_time, "limit": batch_size}

        rows = conn.execute(query, params).fetchall()

        if not rows:
            logger.info("✓ 업데이트가 필요한 종목이 없습니다.")
            return

        logger.info(f"{'=' * 60}")
        logger.info(f"총 {len(rows)}개 종목의 분할 정보를 업데이트합니다...")
        logger.info(f"{'=' * 60}")

        success_count = 0
        error_count = 0
        split_found_count = 0

        for i, (ticker, old_split_date, old_updated_at) in enumerate(rows, 1):
            try:
                logger.info(f"[{i}/{len(rows)}] {ticker} 처리 중...")

                # yfinance에서 분할 정보 조회
                stock = yf.Ticker(ticker)
                splits = stock.splits

                last_split_date = None
                last_split_ratio = None

                if splits is not None and not splits.empty:
                    last_split_timestamp = splits.index[-1]
                    last_split_date = pd.to_datetime(last_split_timestamp).date()
                    last_split_ratio = float(splits.iloc[-1])
                    split_found_count += 1

                # DB 업데이트
                update_query = text("""
                    UPDATE stocks
                    SET last_split_date = :split_date,
                        last_split_ratio = :split_ratio,
                        splits_updated_at = :updated_at
                    WHERE ticker = :ticker
                """)

                conn.execute(update_query, {
                    "ticker": ticker,
                    "split_date": last_split_date.isoformat() if last_split_date else None,
                    "split_ratio": last_split_ratio,
                    "updated_at": datetime.utcnow()
                })
                conn.commit()

                if last_split_date:
                    change_marker = ""
                    if old_split_date and old_split_date != last_split_date:
                        change_marker = f" (변경: {old_split_date} → {last_split_date})"
                        
                        # [Split Auto-Correction]
                        # 분할 정보가 변경되었으므로, 기존 가격 데이터는 오염되었을 가능성이 높음.
                        # 따라서 daily_prices를 삭제하고 재수집을 시도함.
                        logger.warning(f"  ⚠ {ticker}: 분할 정보 변경 감지! 데이터 정합성을 위해 재수집을 진행합니다.")
                        try:
                            # 1. 기존 데이터 삭제
                            conn.execute(text("DELETE FROM daily_prices WHERE stock_id = (SELECT id FROM stocks WHERE ticker = :t)"), {"t": ticker})
                            conn.commit()
                            logger.info(f"  ✓ {ticker}: 기존 가격 데이터 삭제 완료")
                            
                            # 2. 데이터 재수집 (최근 10년 치)
                            # 주의: 여기서 data_fetcher를 직접 사용
                            from app.utils.data_fetcher import data_fetcher
                            from app.repositories.yfinance_repository import YFinanceRepository
                            
                            repo = YFinanceRepository()
                            start_date = date.today() - timedelta(days=365*10)
                            end_date = date.today()
                            
                            logger.info(f"  ↻ {ticker}: 데이터 재수집 시작 ({start_date} ~ {end_date})...")
                            df_new = data_fetcher.fetch_stock_data(ticker, start_date, end_date, use_cache=False)
                            
                            if df_new is not None and not df_new.empty:
                                repo.save_ticker_data(ticker, df_new)
                                logger.info(f"  ✓ {ticker}: 재수집 및 저장 완료 ({len(df_new)}행)")
                            else:
                                logger.error(f"  ✗ {ticker}: 재수집 실패 (데이터 없음)")
                                
                        except Exception as e:
                            logger.error(f"  ✗ {ticker}: 데이터 자동 보정 실패 - {e}")

                    logger.info(
                        f"  ✓ {ticker}: 분할 날짜 = {last_split_date}, "
                        f"비율 = {last_split_ratio}{change_marker}"
                    )
                else:
                    logger.debug(f"  ✓ {ticker}: 분할 이력 없음")

                success_count += 1

                # Rate limiting (초당 2개 종목) - 재수집 시에는 조금 더 쉬어줌
                time.sleep(1.0 if 'change_marker' in locals() and change_marker else 0.5)

                # [Smart Validation: Price Continuity Check]
                # 메타데이터는 변경되지 않았더라도(이미 최신이라도),
                # DB에 저장된 실제 가격 데이터가 "분할 전/후가 섞여있는지" 확인해야 함.
                # 예: 넷플릭스(NFLX) 10:1 분할.
                #     DB에 11월 11일(500불), 11월 17일 분할, 11월 22일(50불) 이렇게 섞여있으면
                #     11월 16일(500불) -> 11월 17일(50불) 로 90% 폭락하는 대참사가 백테스트에서 발생.
                # 따라서, "마지막 분할 날짜" 주변의 가격 연속성을 검사하여, 비정상적인 괴리가 있으면 재수집 트리거.

                if last_split_date and not change_marker:  # 메타데이터 변경이 없었을 때만 검사 (변경됐으면 이미 위에서 재수집함)
                    try:
                        # 분할일(D)과 그 전 거래일(D-1)의 종가를 가져옴
                        # (정확히 D, D-1이 휴일일 수 있으므로, split_date 이하의 날짜 중 최근 2개를 가져옴)
                        check_query = text("""
                            SELECT date, close 
                            FROM daily_prices 
                            WHERE stock_id = (SELECT id FROM stocks WHERE ticker = :t)
                              AND date <= :split_date
                            ORDER BY date DESC
                            LIMIT 2
                        """)
                        price_rows = conn.execute(check_query, {"t": ticker, "split_date": last_split_date}).fetchall()
                        
                        if len(price_rows) == 2:
                            # d0: 분할일(또는 그 직전 거래일 중 더 최근), d1: 그 전 거래일
                            d0_date, d0_close = price_rows[0]
                            d1_date, d1_close = price_rows[1]
                            
                            if d0_close > 0:
                                ratio = d1_close / d0_close
                                
                                # 분할 비율(split_ratio)과 비교?
                                # 보통 주식 분할은 2:1, 10:1 등 가격이 낮아짐 -> ratio가 2.0, 10.0 등이 됨 (d1 > d0)
                                # 만약 이미 보정된(Adjusted) 데이터라면 ratio는 1.0 근처여야 함 (하루만에 50% 폭락은 드무니까)
                                # 따라서 ratio가 1.5 이상이면 "보정되지 않은 데이터가 섞여있음"으로 강력히 의심 가능.
                                
                                # 임계값: 1.8 (약 -45% 이상의 하락). 일반적인 시장 붕괴로도 -45%는 하루만에 잘 안일어남.
                                if ratio > 1.8:
                                    logger.warning(
                                            f"  ⚠ {ticker}: 가격 불연속성 감지! (Date: {d1_date}->{d0_date}, Price: {d1_close}->{d0_close}, Ratio: {ratio:.2f}) "
                                            f"분할 반영이 안 된 데이터가 섞여있습니다. 재수집합니다."
                                    )
                                    
                                    # --- 재수집 로직 (위와 동일하므로 함수로 빼는게 좋겠지만 일단 중복 구현) ---
                                    # 1. 기존 데이터 삭제
                                    conn.execute(text("DELETE FROM daily_prices WHERE stock_id = (SELECT id FROM stocks WHERE ticker = :t)"), {"t": ticker})
                                    conn.commit()
                                    logger.info(f"  ✓ {ticker}: 오염된 가격 데이터 삭제 완료")
                                    
                                    # 2. 데이터 재수집
                                    from app.utils.data_fetcher import data_fetcher
                                    from app.repositories.yfinance_repository import YFinanceRepository
                                    
                                    repo = YFinanceRepository()
                                    start_date = date.today() - timedelta(days=365*10)
                                    end_date = date.today()
                                    
                                    logger.info(f"  ↻ {ticker}: 데이터 재수집 시작 ({start_date} ~ {end_date})...")
                                    df_new = data_fetcher.fetch_stock_data(ticker, start_date, end_date, use_cache=False)
                                    
                                    if df_new is not None and not df_new.empty:
                                        repo.save_ticker_data(ticker, df_new)
                                        logger.info(f"  ✓ {ticker}: 재수집 및 저장 완료 ({len(df_new)}행)")
                                    else:
                                        logger.error(f"  ✗ {ticker}: 재수집 실패 (데이터 없음)")

                    except Exception as e:
                        logger.error(f"  ✗ {ticker}: 가격 연속성 검사 중 오류 - {e}")

            except Exception as e:
                logger.error(f"  ✗ {ticker}: 업데이트 실패 - {e}")
                error_count += 1
                continue

        logger.info(f"{'=' * 60}")
        logger.info(f"완료: 성공 {success_count}개, 실패 {error_count}개")
        logger.info(f"분할 이력 발견: {split_found_count}개")
        logger.info(f"{'=' * 60}")

    except Exception as e:
        logger.error(f"배치 작업 실패: {e}")
        raise
    finally:
        conn.close()


def get_split_stats():
    """분할 정보 통계 조회"""
    engine = DatabaseConnectionManager.get_engine()
    conn = engine.connect()

    try:
        stats_query = text("""
            SELECT
                COUNT(*) as total_stocks,
                COUNT(last_split_date) as stocks_with_splits,
                COUNT(splits_updated_at) as stocks_updated,
                MIN(splits_updated_at) as oldest_update,
                MAX(splits_updated_at) as newest_update
            FROM stocks
        """)

        result = conn.execute(stats_query).fetchone()

        if result:
            total, with_splits, updated, oldest, newest = result

            logger.info(f"{'=' * 60}")
            logger.info("분할 메타데이터 통계")
            logger.info(f"{'=' * 60}")
            logger.info(f"전체 종목 수: {total}")
            logger.info(f"분할 이력 있는 종목: {with_splits} ({with_splits/total*100:.1f}%)")
            logger.info(f"업데이트된 종목: {updated} ({updated/total*100:.1f}%)")
            logger.info(f"가장 오래된 업데이트: {oldest}")
            logger.info(f"가장 최근 업데이트: {newest}")
            logger.info(f"{'=' * 60}")

    except Exception as e:
        logger.error(f"통계 조회 실패: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description='주가 분할 메타데이터 업데이트',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 7일 이상 된 종목만 50개씩 업데이트
  python scripts/update_split_metadata.py

  # 모든 종목 강제 업데이트 (100개씩)
  python scripts/update_split_metadata.py --all --batch-size 100

  # 통계만 조회
  python scripts/update_split_metadata.py --stats-only
        """
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='한 번에 처리할 종목 수 (기본: 50)'
    )
    parser.add_argument(
        '--max-age-days',
        type=int,
        default=7,
        help='업데이트 대상 기준 일수 (기본: 7일)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='모든 종목 강제 업데이트'
    )
    parser.add_argument(
        '--stats-only',
        action='store_true',
        help='통계만 조회하고 업데이트는 하지 않음'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("주가 분할 메타데이터 업데이트 스크립트")
    logger.info("=" * 60)

    # 통계 조회
    get_split_stats()

    # 업데이트 실행
    if not args.stats_only:
        logger.info("")
        logger.info(f"설정:")
        logger.info(f"  - 배치 크기: {args.batch_size}")
        logger.info(f"  - 최대 age: {args.max_age_days}일")
        logger.info(f"  - 강제 업데이트: {args.all}")
        logger.info("")

        update_split_metadata_batch(
            batch_size=args.batch_size,
            max_age_days=args.max_age_days,
            force_all=args.all
        )

        # 업데이트 후 통계 다시 조회
        logger.info("")
        get_split_stats()
    else:
        logger.info("통계만 조회합니다 (--stats-only)")
