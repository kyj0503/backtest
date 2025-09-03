"""
백테스팅 API
"""
from fastapi import APIRouter, HTTPException, status
from ....models.requests import BacktestRequest
from ....models.responses import BacktestResult, ErrorResponse, ChartDataResponse
from ....models.schemas import PortfolioBacktestRequest
from ....services.backtest_service import backtest_service
from ....services.portfolio_service import PortfolioBacktestService
from ....services.yfinance_db import load_ticker_data
from ....utils.data_fetcher import data_fetcher
from ....core.custom_exceptions import (
    DataNotFoundError, 
    InvalidSymbolError, 
    YFinanceRateLimitError,
    ValidationError,
    handle_yfinance_error
)
from ....utils.user_messages import get_user_friendly_message, log_error_for_debugging
import logging
import traceback

logger = logging.getLogger(__name__)
router = APIRouter()
portfolio_service = PortfolioBacktestService()


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
    """
    try:
        # v2 방식: DB에서 데이터 로드 시도
        df = load_ticker_data(request.ticker, request.start_date, request.end_date)
        
        if df is not None and not df.empty:
            # DB 데이터가 있으면 사용 (v2 방식)
            original_get = data_fetcher.get_stock_data

            def _get_stock_data_override(*args, **kwargs):
                return df

            data_fetcher.get_stock_data = _get_stock_data_override

            try:
                result = await backtest_service.run_backtest(request)
                logger.info(f"백테스트 API 완료 (DB 소스): {request.ticker}")
                return result
            finally:
                data_fetcher.get_stock_data = original_get
        else:
            # DB에 데이터가 없으면 기존 v1 방식 사용
            backtest_service.validate_backtest_request(request)
            result = await backtest_service.run_backtest(request)
            logger.info(f"백테스트 API 완료 (yfinance 소스): {request.ticker}")
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
    """
    try:
        # v2 방식: DB에서 데이터 로드 시도
        df = load_ticker_data(request.ticker, request.start_date, request.end_date)
        
        if df is not None and not df.empty:
            # DB 데이터가 있으면 사용 (v2 방식)
            original_get = data_fetcher.get_stock_data

            def _get_stock_data_override(*args, **kwargs):
                return df

            data_fetcher.get_stock_data = _get_stock_data_override

            try:
                chart_data = await backtest_service.generate_chart_data(request)
                logger.info(f"차트 데이터 API 완료 (DB 소스): {request.ticker}, 데이터 포인트: {len(chart_data.ohlc_data)}")
                return chart_data
            finally:
                data_fetcher.get_stock_data = original_get
        else:
            # DB에 데이터가 없으면 기존 v1 방식 사용
            backtest_service.validate_backtest_request(request)
            chart_data = await backtest_service.generate_chart_data(request)
            logger.info(f"차트 데이터 API 완료 (yfinance 소스): {request.ticker}, 데이터 포인트: {len(chart_data.ohlc_data)}")
            return chart_data
        
    except ValueError as e:
        from app.core.custom_exceptions import ValidationError
        from app.utils.user_messages import get_user_friendly_message, log_error_for_debugging
        
        error_id = log_error_for_debugging(e, "차트 데이터 요청", {"ticker": request.ticker})
        logger.error(f"[{error_id}] 차트 데이터 요청 오류: {str(e)}")
        
        raise ValidationError(
            get_user_friendly_message("ValidationError", str(e))
        )
    
    except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError) as e:
        # 이미 적절한 HTTP 상태코드와 메시지를 가진 커스텀 예외들은 그대로 전파
        raise e
        
    except Exception as e:
        from app.utils.user_messages import get_user_friendly_message, log_error_for_debugging
        from app.core.custom_exceptions import handle_yfinance_error
        
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