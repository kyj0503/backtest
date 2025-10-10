"""
백테스팅 API
"""
from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional
from ....models.requests import BacktestRequest, UnifiedBacktestRequest
from ....models.responses import BacktestResult, ErrorResponse, ChartDataResponse
from ....models.schemas import PortfolioBacktestRequest, PortfolioStock
from ....services.backtest_service import backtest_service
from ....services.portfolio_service import PortfolioService
from ....services.data_service import data_service
from ....core.exceptions import (
    DataNotFoundError, 
    InvalidSymbolError, 
    YFinanceRateLimitError,
    ValidationError,
    handle_yfinance_error
)
from ....core.config import settings
from ....utils.user_messages import get_user_friendly_message, log_error_for_debugging
from ..decorators import handle_backtest_errors, handle_portfolio_errors
import logging
import traceback
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter()
portfolio_service = PortfolioService()


@router.post(
    "/portfolio",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행 (통합 응답)",
    description="여러 자산으로 구성된 포트폴리오의 백테스트를 실행하고 모든 필요한 데이터를 한번에 반환합니다."
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """
    포트폴리오 백테스트 실행 API (통합 응답)
    
    백테스트 실행 후 프론트엔드에서 필요한 모든 데이터를 하나의 응답으로 통합하여 반환합니다:
    - 백테스트 결과 (수익률, 통계 등)
    - 주가 데이터 (각 종목)
    - 환율 데이터
    - 급등/급락 이벤트 & 뉴스
    - 벤치마크 데이터 (S&P 500, NASDAQ)
    
    이를 통해 프론트엔드에서의 추가 API 호출을 제거하고 성능을 개선합니다.
    
    **요청 파라미터**:
    - **portfolio**: 포트폴리오 구성 (종목, 비중, 투자방식 등)
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    - **commission**: 수수료율 (0 ~ 0.1)
    - **rebalance_frequency**: 리밸런싱 주기 (monthly, quarterly, yearly)
    - **strategy**: 전략명 (기본: buy_and_hold)
    
    **통합 응답**:
    ```json
    {
      "status": "success",
      "data": {
        "portfolio_statistics": { ... },
        "equity_curve": { ... },
        "individual_returns": { ... },
        "stock_data": { "AAPL": [...], "GOOGL": [...] },
        "exchange_rates": [...],
        "volatility_events": { "AAPL": [...] },
        "sp500_benchmark": [...],
        "nasdaq_benchmark": [...]
      }
    }
    ```
    """
    # 1. 백테스트 실행
    backtest_result = await portfolio_service.run_portfolio_backtest(request)
    
    if backtest_result.get('status') != 'success':
        return backtest_result
    
    # 2. 추가 데이터 수집을 위한 준비
    symbols = list(set([item.symbol for item in request.portfolio if item.symbol.upper() not in ['CASH', '현금']]))
    start_date = request.start_date
    end_date = request.end_date
    
    # 3. 주가 데이터 수집 (병렬)
    stock_data = {}
    for symbol in symbols:
        try:
            df = data_service.get_ticker_data_sync(symbol, start_date, end_date)
            if df is not None and not df.empty:
                stock_data[symbol] = [
                    {
                        'date': date.strftime('%Y-%m-%d'),
                        'price': float(row['Close']),
                        'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
                    }
                    for date, row in df.iterrows()
                ]
        except Exception as e:
            logger.warning(f"주가 데이터 수집 실패: {symbol} - {str(e)}")
            stock_data[symbol] = []
    
    # 4. 환율 데이터 수집
    exchange_rates = []
    try:
        exchange_data = data_service.get_ticker_data_sync(
            settings.exchange_rate_ticker,
            start_date,
            end_date
        )
        if exchange_data is not None and not exchange_data.empty:
            exchange_rates = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'rate': float(row['Close'])
                }
                for date, row in exchange_data.iterrows()
            ]
    except Exception as e:
        logger.warning(f"환율 데이터 수집 실패: {str(e)}")
    
    # 5. 급등/급락 이벤트 수집 (5% 이상 변동)
    volatility_events = {}
    for symbol in symbols:
        try:
            df = data_service.get_ticker_data_sync(symbol, start_date, end_date)
            if df is not None and not df.empty:
                df['daily_return'] = df['Close'].pct_change() * 100
                significant_moves = df[abs(df['daily_return']) >= 5.0].copy()
                
                events = []
                for date, row in significant_moves.iterrows():
                    events.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'daily_return': float(row['daily_return']),
                        'close_price': float(row['Close']),
                        'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0,
                        'event_type': '급등' if row['daily_return'] > 0 else '급락'
                    })
                
                events.sort(key=lambda x: x['date'], reverse=True)
                volatility_events[symbol] = events[:10]  # 상위 10개만
        except Exception as e:
            logger.warning(f"급등락 이벤트 수집 실패: {symbol} - {str(e)}")
            volatility_events[symbol] = []
    
    # 6. 벤치마크 데이터 수집 (S&P 500, NASDAQ)
    sp500_benchmark = []
    nasdaq_benchmark = []
    
    try:
        sp500_data = data_service.get_ticker_data_sync('^GSPC', start_date, end_date)
        if sp500_data is not None and not sp500_data.empty:
            sp500_benchmark = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close'])
                }
                for date, row in sp500_data.iterrows()
            ]
    except Exception as e:
        logger.warning(f"S&P 500 벤치마크 데이터 수집 실패: {str(e)}")
    
    try:
        nasdaq_data = data_service.get_ticker_data_sync('^IXIC', start_date, end_date)
        if nasdaq_data is not None and not nasdaq_data.empty:
            nasdaq_benchmark = [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close'])
                }
                for date, row in nasdaq_data.iterrows()
            ]
    except Exception as e:
        logger.warning(f"NASDAQ 벤치마크 데이터 수집 실패: {str(e)}")
    
    # 7. 통합 응답 생성
    backtest_result['data']['stock_data'] = stock_data
    backtest_result['data']['exchange_rates'] = exchange_rates
    backtest_result['data']['volatility_events'] = volatility_events
    backtest_result['data']['sp500_benchmark'] = sp500_benchmark
    backtest_result['data']['nasdaq_benchmark'] = nasdaq_benchmark
    
    logger.info(f"통합 백테스트 응답 생성 완료: {len(symbols)}개 종목, {len(exchange_rates)}개 환율 데이터")
    
    return backtest_result


# ========================================
# 아래 엔드포인트들은 더 이상 사용하지 않습니다.
# 모든 데이터는 POST /portfolio 엔드포인트의 통합 응답에 포함됩니다.
# ========================================
