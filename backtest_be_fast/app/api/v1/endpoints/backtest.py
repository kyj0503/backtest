"""
백테스팅 API
"""
from fastapi import APIRouter, HTTPException, status, Request
from typing import Optional
from ....models.requests import BacktestRequest, UnifiedBacktestRequest
from ....models.responses import BacktestResult, ErrorResponse, ChartDataResponse
from ....models.schemas import PortfolioBacktestRequest, PortfolioStock
from ....services.backtest_service import backtest_service
from ....services.portfolio_service import PortfolioBacktestService
from ....services.yfinance_db import load_ticker_data
from ....core.custom_exceptions import (
    DataNotFoundError, 
    InvalidSymbolError, 
    YFinanceRateLimitError,
    ValidationError,
    handle_yfinance_error
)
from ....events.event_system import event_system_manager
from ....utils.user_messages import get_user_friendly_message, log_error_for_debugging
import logging
import traceback
import pandas as pd
from datetime import datetime


logger = logging.getLogger(__name__)
router = APIRouter()
portfolio_service = PortfolioBacktestService()


@router.get(
    "/metrics",
    summary="백테스트 메트릭 요약",
    description="이벤트 시스템에서 집계된 백테스트 메트릭(성공률, 전략별 성과 등)을 반환합니다."
)
async def get_backtest_metrics():
    """백테스트 메트릭 요약 반환 API"""
    return event_system_manager.get_backtest_metrics()


@router.get(
    "/notifications",
    summary="백테스트 알림 조회",
    description="이벤트 시스템에서 수집된 백테스트 알림(성과, 실패 등)을 반환합니다."
)
async def get_backtest_notifications(limit: int = 20):
    """백테스트 알림 반환 API"""
    return event_system_manager.get_backtest_notifications(limit)


@router.get(
    "/portfolio-analytics",
    summary="포트폴리오 분석 통계 조회",
    description="이벤트 시스템에서 집계된 포트폴리오 분석/통계 데이터를 반환합니다. portfolio_id로 특정 포트폴리오만 조회 가능."
)
async def get_portfolio_analytics(portfolio_id: str = None):
    """포트폴리오 분석 결과 반환 API"""
    return event_system_manager.get_portfolio_analytics(portfolio_id)


@router.get(
    "/portfolio-alerts",
    summary="포트폴리오 경고/알림 조회",
    description="이벤트 시스템에서 수집된 포트폴리오 경고/알림을 반환합니다. portfolio_id로 특정 포트폴리오만 조회 가능."
)
async def get_portfolio_alerts(portfolio_id: str = None, limit: int = 20):
    """포트폴리오 경고 반환 API"""
    return event_system_manager.get_portfolio_alerts(portfolio_id, limit)


@router.post(
    "/run",
    response_model=BacktestResult,
    status_code=status.HTTP_200_OK,
    summary="백테스트 실행",
    description="주어진 전략과 파라미터로 백테스트를 실행합니다. (DB 소스 우선 사용)"
)
async def run_backtest(request: BacktestRequest):
    """
    백테스트 실행 API (v2 개선사항 적용)
    
    - **ticker**: 주식 티커 심볼 (예: AAPL, GOOGL)
    - **start_date**: 백테스트 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 백테스트 종료 날짜 (YYYY-MM-DD)
    - **initial_cash**: 초기 투자금액
    - **strategy**: 사용할 전략명
    - **strategy_params**: 전략별 파라미터 (선택사항)
    - **commission**: 거래 수수료 (기본값: 0.002)
    
    v2 개선사항: DB에서 데이터를 우선 사용하고, 없을 경우 yfinance 사용
    로그인 사용자는 백테스트 히스토리가 자동으로 저장됩니다.
    """
    # 모든 요청을 게스트로 처리합니다.
    
    try:
        result = await backtest_service.run_backtest(request)
        logger.info(f"백테스트 API 완료: {request.ticker}")

        # 히스토리 저장 기능은 제거되었습니다.

        return result

    except ValueError as e:
        logger.error(f"백테스트 요청 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"백테스트 실행 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="백테스트 실행 중 오류가 발생했습니다."
        )


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
    
    try:
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
        
    except ValueError as e:
        from app.utils.user_messages import get_user_friendly_message, log_error_for_debugging

        error_id = log_error_for_debugging(e, "차트 데이터 요청", {"ticker": request.ticker})
        logger.error(f"[{error_id}] 차트 데이터 요청 오류: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=get_user_friendly_message("ValidationError", str(e))
        )

    except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError, ValidationError) as e:
        # 이미 적절한 HTTP 상태코드와 메시지를 가진 커스텀 예외들은 그대로 전파
        # ValidationError는 422 Unprocessable Entity로 처리
        if isinstance(e, ValidationError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        raise e
        
    except Exception as e:
        from app.utils.user_messages import get_user_friendly_message, log_error_for_debugging
        from app.core.custom_exceptions import handle_yfinance_error
        from app.utils.data_fetcher import InvalidSymbolError as DataFetcherInvalidSymbolError
        
        # InvalidSymbolError인지 먼저 확인
        if isinstance(e, DataFetcherInvalidSymbolError) or "InvalidSymbolError" in str(type(e)) or "'는 유효하지 않은 종목 심볼입니다" in str(e):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        
        error_id = log_error_for_debugging(e, "차트 데이터 생성", {
            "ticker": request.ticker,
            "start_date": str(request.start_date),
            "end_date": str(request.end_date)
        })
        
        # yfinance 관련 에러인지 확인
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ["yfinance", "yahoo", "ticker", "symbol", "no data"]):
            raise handle_yfinance_error(e, request.ticker, str(request.start_date), str(request.end_date))
        
        logger.error(f"[{error_id}] 차트 데이터 생성 예상치 못한 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"차트 데이터 생성 중 예상치 못한 오류가 발생했습니다. (오류 ID: {error_id})"
        )


@router.post(
    "/portfolio",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행",
    description="여러 종목으로 구성된 포트폴리오의 백테스트를 실행합니다."
)
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
    try:
        # 입력 검증
        if not request.portfolio or len(request.portfolio) == 0:
            raise ValidationError("포트폴리오가 비어있습니다. 최소 1개 종목을 추가해주세요.")
        
        if len(request.portfolio) > 10:
            raise ValidationError("포트폴리오는 최대 10개 종목까지 포함할 수 있습니다.")
        
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
        
    except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError, ValidationError) as e:
        # 사용자 친화적 오류 처리
        user_message = get_user_friendly_message(type(e).__name__, str(e))
        logger.warning(f"User error in portfolio backtest: {user_message}")
        raise HTTPException(status_code=400, detail=user_message)
        
    except HTTPException:
        # 이미 처리된 HTTP 예외는 재발생
        raise
        
    except Exception as e:
        # 예상하지 못한 오류 처리
        error_id = log_error_for_debugging(e, "portfolio_backtest", {
            "portfolio_size": len(request.portfolio) if request.portfolio else 0,
            "strategy": getattr(request, 'strategy', 'buy_and_hold'),
            "date_range": f"{request.start_date} to {request.end_date}"
        })
        
        logger.error(f"Unexpected error in portfolio backtest [ID: {error_id}]: {str(e)}")
        logger.debug(traceback.format_exc())
        
        user_message = get_user_friendly_message("unexpected_error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{user_message} (오류 ID: {error_id})"
        )


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
    threshold: float = 5.0  # 기본 5% 임계값
):
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
        # KRW=X 티커로 원달러 환율 데이터 조회
        exchange_data = load_ticker_data("KRW=X", start_date, end_date)
        
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
        # KRW=X 티커로 원달러 환율 데이터 조회
        exchange_data = load_ticker_data("KRW=X", start_date, end_date)
        
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



@router.post(
    "/execute",
    status_code=status.HTTP_200_OK,
    summary="통합 백테스트 실행",
    description="단일 종목 또는 포트폴리오 백테스트를 자동으로 구분하여 실행합니다."
)
async def execute_backtest(request: UnifiedBacktestRequest, request_obj: Request = None):
    """
    통합 백테스트 실행 API
    
    단일 종목과 포트폴리오를 자동으로 구분하여 적절한 백테스트 엔진을 사용합니다.
    결과는 표준화된 형식으로 반환됩니다.
    
    **판별 기준:**
    - 포트폴리오에 종목이 1개이고 현금 자산이 없으면: 단일 종목 백테스트
    - 포트폴리오에 종목이 여러개이거나 현금 자산이 있으면: 포트폴리오 백테스트
    
    **요청 예시:**
    ```json
    {
        "portfolio": [
            {"symbol": "AAPL", "amount": 10000, "asset_type": "stock"},
            {"symbol": "GOOGL", "amount": 5000, "asset_type": "stock"}
        ],
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "strategy": "buy_and_hold"
    }
    ```
    """
    try:
        # Temporary debug: log raw incoming body and some headers to help reproduce client-side 500
        try:
            if request_obj is not None:
                raw = await request_obj.body()
                logger.debug("[debug] execute_backtest raw_body: %s", raw.decode('utf-8', errors='replace'))
                # log a few headers
                hdrs = {k: v for k, v in request_obj.headers.items() if k.lower() in ['content-type', 'origin', 'host']}
                logger.debug("[debug] execute_backtest headers: %s", hdrs)
        except Exception:
            logger.debug("[debug] failed to read raw request body for execute_backtest")
        # 현금 자산 여부 확인
        has_cash_asset = any(asset.asset_type == 'cash' for asset in request.portfolio)
        
        # 추가 데이터 수집 (환율, 벤치마크) - 백테스트 실행 전에 공통으로 수집
        additional_data = {}
        try:
            # 원달러 환율 데이터
            exchange_data = load_ticker_data("KRW=X", str(request.start_date), str(request.end_date))
            if exchange_data is not None and not exchange_data.empty:
                exchange_rates = []
                for date_idx, row in exchange_data.iterrows():
                    exchange_rates.append({
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "rate": float(row['Close']),
                        "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
                    })
                additional_data["exchange_rates"] = exchange_rates
            
            # S&P 500 벤치마크 데이터
            sp500_data = load_ticker_data("^GSPC", str(request.start_date), str(request.end_date))
            if sp500_data is not None and not sp500_data.empty:
                benchmark_data = []
                for date_idx, row in sp500_data.iterrows():
                    benchmark_data.append({
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "close": float(row['Close']),
                        "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
                    })
                additional_data["sp500_benchmark"] = benchmark_data
            
            # 나스닥 벤치마크 데이터
            nasdaq_data = load_ticker_data("^IXIC", str(request.start_date), str(request.end_date))
            if nasdaq_data is not None and not nasdaq_data.empty:
                nasdaq_benchmark = []
                for date_idx, row in nasdaq_data.iterrows():
                    nasdaq_benchmark.append({
                        "date": date_idx.strftime('%Y-%m-%d'),
                        "close": float(row['Close']),
                        "volume": int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
                    })
                additional_data["nasdaq_benchmark"] = nasdaq_benchmark
            
        except Exception as e:
            logger.warning(f"추가 데이터 수집 실패: {str(e)}")
            # 추가 데이터 수집 실패가 전체 백테스트를 실패시키지 않도록
        
        # 단일 종목 vs 포트폴리오 판별
        if len(request.portfolio) == 1 and not has_cash_asset:
            # 단일 종목 백테스트 실행
            asset = request.portfolio[0]
            single_request = BacktestRequest(
                ticker=asset.symbol,
                start_date=str(request.start_date),  # 문자열로 변환
                end_date=str(request.end_date),      # 문자열로 변환
                initial_cash=asset.amount,
                strategy=request.strategy,
                strategy_params=request.strategy_params or {},
                commission=request.commission
            )
            
            # 단일 종목 백테스트 실행
            result = await backtest_service.run_backtest(single_request)
            
            # 차트 데이터 생성 (상세 정보 포함)
            chart_data = await backtest_service.generate_chart_data(single_request, result)
            
            # 응답을 표준화된 형식으로 변환 (포트폴리오와 유사한 구조)
            return {
                "status": "success",
                "backtest_type": "single_stock",
                "data": {
                    "ticker": asset.symbol,
                    "strategy": request.strategy,
                    "start_date": str(request.start_date),
                    "end_date": str(request.end_date),
                    "portfolio_composition": [
                        {
                            "symbol": asset.symbol,
                            "weight": 1.0,
                            "amount": asset.amount,
                            "asset_type": asset.asset_type or "stock"
                        }
                    ],
                    "summary_stats": {
                        "total_return_pct": result.total_return_pct,
                        "annualized_return_pct": result.annualized_return_pct,
                        "buy_and_hold_return_pct": result.buy_and_hold_return_pct,
                        "sharpe_ratio": result.sharpe_ratio,
                        "sortino_ratio": result.sortino_ratio,
                        "max_drawdown_pct": result.max_drawdown_pct,
                        "volatility_pct": result.volatility_pct,
                        "total_trades": result.total_trades,
                        "win_rate_pct": result.win_rate_pct,
                        "profit_factor": result.profit_factor
                    },
                    
                    # 차트 데이터 추가 (포트폴리오와 호환 가능한 형태)
                    "ohlc_data": chart_data.ohlc_data if hasattr(chart_data, 'ohlc_data') else [],
                    "equity_data": chart_data.equity_data if hasattr(chart_data, 'equity_data') else [],
                    "trade_markers": chart_data.trade_markers if hasattr(chart_data, 'trade_markers') else [],
                    "indicators": chart_data.indicators if hasattr(chart_data, 'indicators') else [],
                    
                    # 포트폴리오 형식과 호환을 위한 추가 데이터
                    "individual_results": [{
                        "ticker": asset.symbol,
                        "final_equity": result.final_equity,
                        "total_return_pct": result.total_return_pct,
                        "sharpe_ratio": result.sharpe_ratio,
                        "weight": 1.0,
                        "amount": asset.amount,
                        "trades": result.total_trades,
                        "win_rate": result.win_rate_pct
                    }],
                    "portfolio_result": {
                        "total_equity": result.final_equity,
                        "total_return_pct": result.total_return_pct
                    },
                    
                    # 추가 데이터 (환율, 벤치마크 등)
                    **additional_data
                }
            }
            
        else:
            # 포트폴리오 백테스트 실행
            portfolio_request = PortfolioBacktestRequest(
                portfolio=[
                    PortfolioStock(
                        symbol=asset.symbol,
                        amount=asset.amount,
                        investment_type=asset.investment_type or "lump_sum",
                        dca_periods=asset.dca_periods or 12,
                        asset_type=asset.asset_type or "stock"
                    ) for asset in request.portfolio
                ],
                start_date=str(request.start_date),  # 문자열로 변환
                end_date=str(request.end_date),      # 문자열로 변환
                commission=request.commission,
                rebalance_frequency=request.rebalance_frequency or "monthly",
                strategy=request.strategy,
                strategy_params=request.strategy_params or {}
            )
            
            result = await portfolio_service.run_portfolio_backtest(portfolio_request)
            
            # 추가 데이터를 결과에 병합
            logger.info(f"추가 데이터 키: {list(additional_data.keys())}")
            logger.info(f"포트폴리오 서비스 결과 구조: {list(result.keys()) if isinstance(result, dict) else 'not a dict'}")
            
            if "data" in result:
                logger.info(f"result['data'] 병합 전 키: {list(result['data'].keys()) if isinstance(result['data'], dict) else 'not a dict'}")
                result["data"].update(additional_data)
                logger.info(f"result['data'] 병합 후 키: {list(result['data'].keys())}")
            else:
                logger.warning("result에 'data' 키가 없습니다. 전체 result에 병합합니다.")
                result.update(additional_data)
            
            # 응답을 표준화된 형식으로 변환
            return {
                "status": "success",
                "backtest_type": "portfolio",
                "data": result.get("data", result)
            }
    
    except Exception as e:
        error_id = log_error_for_debugging(e, "execute_backtest", {
            "portfolio_size": len(request.portfolio),
            "strategy": request.strategy,
            "date_range": f"{request.start_date} to {request.end_date}",
        })
        
        logger.error(f"Unified backtest execution failed [ID: {error_id}]: {str(e)}")
        # Debug: include full traceback in logs to help diagnose server-side 500s
        logger.debug(traceback.format_exc())
        user_message = get_user_friendly_message("unexpected_error", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{user_message} (오류 ID: {error_id})"
        ) 
