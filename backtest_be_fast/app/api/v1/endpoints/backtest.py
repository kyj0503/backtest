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
    summary="포트폴리오 백테스트 실행",
    description="여러 자산으로 구성된 포트폴리오의 백테스트를 실행합니다."
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """
    포트폴리오 백테스트 실행 API
    
    여러 자산(주식, 현금 등)으로 구성된 포트폴리오의 백테스트를 실행하고
    리밸런싱을 포함한 성과를 분석합니다.
    
    - **portfolio**: 포트폴리오 구성 (종목, 비중, 투자방식 등)
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    - **commission**: 수수료율 (0 ~ 0.1)
    - **rebalance_frequency**: 리밸런싱 주기 (monthly, quarterly, yearly)
    - **strategy**: 전략명 (기본: buy_and_hold)
    
    반환값: 포트폴리오 성과 지표, 자산별 수익률, 리밸런싱 내역 등
    """
    return await portfolio_service.run_portfolio_backtest(request)


@router.get(
    "/stock-volatility-news/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="주가 급등/급락일 뉴스 조회",
    description="지정된 기간 중 주가가 5% 이상 변동한 날의 뉴스를 조회합니다."
)
async def get_stock_volatility_news(
    ticker: str,
    start_date: str,
    end_date: str,
    threshold: float = None  # None이면 설정값 사용
):
    # threshold가 지정되지 않으면 설정값 사용
    if threshold is None:
        threshold = settings.volatility_threshold_pct
    """
    주가 급등/급락일 뉴스 조회 API
    
    - **ticker**: 주식 티커 심볼 (예: AAPL, GOOGL)
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    - **threshold**: 변동 임계값 (기본값: 5.0%)
    
    반환값: 급등/급락일과 관련 뉴스
    """
    try:
        # 현금 자산은 변동성 없음
        if ticker.upper() in ['CASH', '현금']:
            return {
                "status": "success",
                "data": {
                    "symbol": ticker,
                    "volatility_events": [],
                    "news_summary": "현금 자산은 가격 변동이 없습니다."
                }
            }
        
        # 주가 데이터 조회 (DataService 사용)
        stock_data = data_service.get_ticker_data_sync(ticker, start_date, end_date)
        
        if stock_data is None or stock_data.empty:
            return {
                "status": "error",
                "message": f"'{ticker}' 주가 데이터를 찾을 수 없습니다.",
                "data": {"volatility_events": []}
            }
        
        # 일일 수익률 계산
        stock_data['daily_return'] = stock_data['Close'].pct_change() * 100
        
        # 급등/급락일 찾기 (절댓값 기준)
        volatility_events = []
        significant_moves = stock_data[abs(stock_data['daily_return']) >= threshold].copy()
        
        for date, row in significant_moves.iterrows():
            volatility_events.append({
                "date": date.strftime('%Y-%m-%d'),
                "daily_return": float(row['daily_return']),
                "close_price": float(row['Close']),
                "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0,
                "event_type": "급등" if row['daily_return'] > 0 else "급락"
            })
        
        # 날짜순 정렬 (최근순)
        volatility_events.sort(key=lambda x: x['date'], reverse=True)
        
        # 상위 10개 이벤트만 반환
        volatility_events = volatility_events[:10]
        
        return {
            "status": "success",
            "data": {
                "symbol": ticker,
                "threshold": threshold,
                "period": f"{start_date} ~ {end_date}",
                "total_events": len(volatility_events),
                "volatility_events": volatility_events
            }
        }
        
    except Exception as e:
        logger.error(f"주가 변동성 분석 중 오류: {str(e)}")
        return {
            "status": "error", 
            "message": f"주가 변동성 분석 실패: {str(e)}",
            "data": {"volatility_events": []}
        }


@router.get(
    "/stock-data/{ticker}",
    status_code=status.HTTP_200_OK,
    summary="주가 데이터 조회",
    description="지정된 기간의 주가 데이터를 조회합니다."
)
async def get_stock_data(
    ticker: str,
    start_date: str,
    end_date: str
):
    """
    주가 데이터 조회 API
    
    - **ticker**: 주식 티커 심볼 (예: AAPL, GOOGL)
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    
    반환값: 날짜별 주가, 거래량 데이터
    """
    try:
        # 현금 자산은 주가 데이터 없음
        if ticker.upper() in ['CASH', '현금']:
            return {
                "status": "success",
                "data": {
                    "symbol": ticker,
                    "price_data": []
                }
            }
        
        # DataService를 통해 데이터 로드 (DB 우선, fallback to yfinance)
        df = data_service.get_ticker_data_sync(ticker, start_date, end_date)
        
        # 데이터 변환
        price_data = []
        for date, row in df.iterrows():
            price_data.append({
                "date": date.strftime('%Y-%m-%d'),
                "price": float(row['Close']),
                "volume": int(row['Volume']) if 'Volume' in row and not pd.isna(row['Volume']) else 0
            })
        
        return {
            "status": "success",
            "data": {
                "symbol": ticker,
                "price_data": price_data
            }
        }
        
    except DataNotFoundError as e:
        error_id = log_error_for_debugging(e, "get_stock_data", {
            "ticker": ticker,
            "date_range": f"{start_date} to {end_date}"
        })
        
        user_message = get_user_friendly_message("data_not_found", str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{user_message} (오류 ID: {error_id})"
        )
        
    except Exception as e:
        error_id = log_error_for_debugging(e, "get_stock_data", {
            "ticker": ticker,
            "date_range": f"{start_date} to {end_date}"
        })
        
        logger.error(f"Unexpected error in get_stock_data [ID: {error_id}]: {str(e)}")
        user_message = get_user_friendly_message("unexpected_error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{user_message} (오류 ID: {error_id})"
        )


@router.get(
    "/exchange-rate",
    status_code=status.HTTP_200_OK,
    summary="원달러 환율 데이터 조회",
    description="지정된 기간의 원달러 환율 데이터를 조회합니다."
)
async def get_exchange_rate(
    start_date: str,
    end_date: str
):
    """
    원달러 환율 데이터 조회 API
    
    - **start_date**: 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 종료 날짜 (YYYY-MM-DD)
    
    반환값: 날짜별 원달러 환율 데이터
    """
    try:
        # DataService를 통해 환율 데이터 조회
        exchange_data = data_service.get_ticker_data_sync(
            settings.exchange_rate_ticker, 
            start_date, 
            end_date
        )
        
        if exchange_data is None or exchange_data.empty:
            return {
                "status": "error",
                "message": "환율 데이터를 가져올 수 없습니다.",
                "data": {"exchange_rates": []}
            }
        
        # 데이터 변환
        exchange_rates = []
        for date, row in exchange_data.iterrows():
            exchange_rates.append({
                "date": date.strftime('%Y-%m-%d'),
                "rate": float(row['Close']),
                "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
            })
        
        return {
            "status": "success",
            "data": {
                "base_currency": "USD",
                "target_currency": "KRW", 
                "exchange_rates": exchange_rates
            }
        }
        
    except Exception as e:
        logger.error(f"환율 데이터 조회 중 오류: {str(e)}")
        return {
            "status": "error",
            "message": f"환율 데이터 조회 실패: {str(e)}",
            "data": {"exchange_rates": []}
        } 
