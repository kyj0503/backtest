"""
기존 stocks 테이블의 info_json에 상장일(first_trade_date) 추가

실행 방법:
    docker exec -it backtest-be-fast-dev python scripts/update_ticker_listing_dates.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import logging
from sqlalchemy import create_engine, text
from app.core.config import settings
from app.utils.data_fetcher import data_fetcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_listing_dates():
    """모든 stocks의 info_json에 상장일 추가"""
    engine = create_engine(settings.database_url)
    
    with engine.begin() as conn:
        # 모든 티커 조회
        result = conn.execute(text("SELECT id, ticker, info_json FROM stocks"))
        stocks = result.fetchall()
        
        logger.info(f"총 {len(stocks)}개 종목의 상장일 업데이트 시작")
        
        updated_count = 0
        failed_count = 0
        
        for idx, (stock_id, ticker, info_json_str) in enumerate(stocks, 1):
            try:
                # 기존 info 파싱
                if info_json_str:
                    info = json.loads(info_json_str)
                else:
                    info = {}
                
                # 이미 상장일이 있으면 스킵
                if info.get('first_trade_date'):
                    logger.info(f"{ticker}: 상장일이 이미 존재 - {info['first_trade_date']}")
                    continue
                
                # Yahoo Finance에서 상장일 조회
                logger.info(f"{ticker}: Yahoo Finance에서 상장일 조회 중...")
                ticker_info = data_fetcher.fetch_ticker_info(ticker)
                first_trade_date = ticker_info.get('first_trade_date')
                
                if first_trade_date:
                    # info에 상장일 추가
                    info['first_trade_date'] = first_trade_date
                    
                    # DB 업데이트
                    conn.execute(
                        text("UPDATE stocks SET info_json = :info WHERE id = :id"),
                        {"info": json.dumps(info), "id": stock_id}
                    )
                    
                    logger.info(f"{ticker}: 상장일 업데이트 완료 - {first_trade_date}")
                    updated_count += 1
                else:
                    logger.warning(f"{ticker}: 상장일 정보 없음")
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"{ticker}: 업데이트 실패 - {e}")
                failed_count += 1
                continue
        
        # with 블록 종료 시 자동 커밋
        logger.info(f"업데이트 완료: 성공 {updated_count}개, 실패 {failed_count}개")


if __name__ == "__main__":
    update_listing_dates()
