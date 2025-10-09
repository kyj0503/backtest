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
from ....services.yfinance_db import load_ticker_data
from ....core.exceptions import (
    DataNotFoundError, 
    InvalidSymbolError, 
    YFinanceRateLimitError,
    ValidationError,
    handle_yfinance_error
)
from ....core.config import settings
from ....events.event_system import event_system_manager
from ....utils.user_messages import get_user_friendly_message, log_error_for_debugging
from ..decorators import handle_backtest_errors, handle_portfolio_errors
import logging
import traceback
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter()
portfolio_service = PortfolioService()



@router.get(
    "/health",
    summary="백테스트 서비스 상태 확인",
    description="백테스트 서비스의 상태를 확인합니다."
)
async def backtest_health():
    """백테스트 서비스 헬스체크"""
    try:
        # 간단한 검증 로직
        from ....utils.data_fetcher import data_fetcher
        
        # 샘플 티커로 간단 검증
        is_healthy = data_fetcher.validate_ticker("AAPL")
        
        if is_healthy:
            return {
                "status": "healthy",
                "message": "백테스트 서비스가 정상 작동 중입니다.",
                "data_source": "Yahoo Finance 연결 정상"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="데이터 소스 연결에 문제가 있습니다."
            )
            
    except Exception as e:
        logger.error(f"헬스체크 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="백테스트 서비스 상태 확인 실패"
        )


@router.post(
    "/chart-data",
    response_model=ChartDataResponse,
    status_code=status.HTTP_200_OK,
    summary="백테스트 차트 데이터",
    description="백테스트 결과를 Recharts용 차트 데이터로 반환합니다. (DB 소스 우선 사용)"
)
@handle_backtest_errors
async def get_chart_data(request: BacktestRequest):
    """
    백테스트 차트 데이터 API (v2 개선사항 적용)
    
    백테스트를 실행하고 결과를 Recharts 라이브러리에서 사용할 수 있는 
    JSON 형태의 차트 데이터로 반환합니다.
    
    **반환 데이터:**
    - **ohlc_data**: 캔들스틱 차트용 OHLC 데이터
    - **equity_data**: 자산 곡선 데이터
    - **trade_markers**: 거래 진입/청산 마커
    - **indicators**: 기술 지표 데이터
    - **summary_stats**: 주요 성과 지표
    
    **사용 예시 (React + Recharts):**
    ```javascript
    // 캔들스틱 차트
    <ComposedChart data={chartData.ohlc_data}>
      <XAxis dataKey="date" />
      <YAxis />
      <Bar dataKey="volume" />
      <Line dataKey="close" />
    </ComposedChart>
    
    // 자산 곡선
    <LineChart data={chartData.equity_data}>
      <Line dataKey="return_pct" stroke="#8884d8" />
      <Line dataKey="drawdown_pct" stroke="#ff0000" />
    </LineChart>
    ```
    
    v2 개선사항: DB에서 데이터를 우선 사용하고, 없을 경우 yfinance 사용
    로그인 사용자는 백테스트 히스토리가 자동으로 저장됩니다.
    """
    # 모든 요청을 게스트로 처리합니다.
    
    # 실제 백테스트를 실행하여 정확한 통계를 얻습니다
    backtest_result = await backtest_service.run_backtest(request)

    chart_data = await backtest_service.generate_chart_data(
        request, backtest_result
    )
    logger.info(
        "차트 데이터 API 완료: %s, 데이터 포인트: %s",
        request.ticker,
        len(chart_data.ohlc_data),
    )

    # 히스토리 저장 기능은 제거되었습니다.

    return chart_data


@router.post(
    "/portfolio",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행",
    description="여러 종목으로 구성된 포트폴리오의 백테스트를 실행합니다."
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """
    포트폴리오 백테스트 실행 API
    
    - **portfolio**: 포트폴리오 구성 (종목과 비중/금액)
    - **start_date**: 백테스트 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 백테스트 종료 날짜 (YYYY-MM-DD)
    - **cash**: 초기 투자금액
    - **commission**: 거래 수수료 (기본값: 0.002)
    - **rebalance_frequency**: 리밸런싱 주기 (monthly, quarterly, yearly)
    
    **사용 예시:**
    ```json
    {
        "portfolio": [
            {"symbol": "AAPL", "amount": 4000, "investment_type": "lump_sum"},
            {"symbol": "GOOGL", "amount": 3000, "investment_type": "dca", "dca_periods": 12},
            {"symbol": "MSFT", "amount": 3000, "investment_type": "lump_sum"}
        ],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "commission": 0.002,
        "rebalance_frequency": "monthly"
    }
    ```
    """
    # 입력 검증
    if not request.portfolio or len(request.portfolio) == 0:
        raise ValidationError("포트폴리오가 비어있습니다. 최소 1개 종목을 추가해주세요.")

    if len(request.portfolio) > settings.max_portfolio_items:
        raise ValidationError(f"포트폴리오는 최대 {settings.max_portfolio_items}개 종목까지 포함할 수 있습니다.")
    
    # 포트폴리오 백테스트 실행
    result = await portfolio_service.run_portfolio_backtest(request)
    
    if result.get('status') == 'error':
        # 서비스에서 반환된 에러 처리
        error_message = result.get('error', '알 수 없는 오류가 발생했습니다.')
        user_message = get_user_friendly_message("portfolio_backtest_error", error_message)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=user_message
        )
    
    logger.info(f"포트폴리오 백테스트 API 완료: {len(request.portfolio)} 종목")
    return result


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
        
        # 주가 데이터 조회
        stock_data = load_ticker_data(ticker, start_date, end_date)
        
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
        
        # DB에서 데이터 로드 시도
        df = load_ticker_data(ticker, start_date, end_date)
        
        if df is None or df.empty:
            # DB에 없으면 yfinance에서 가져오기
            df = data_fetcher.get_stock_data(ticker, start_date, end_date)
            
            if df is None or df.empty:
                raise DataNotFoundError(f"'{ticker}' 종목의 데이터를 찾을 수 없습니다.")
        
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
        # 설정에서 환율 티커 가져오기
        exchange_data = load_ticker_data(settings.exchange_rate_ticker, start_date, end_date)
        
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
