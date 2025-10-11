"""
백테스팅 API 엔드포인트

Controller 역할: 요청 검증 및 응답 반환만 수행
비즈니스 로직은 서비스 레이어에 위임
"""
from fastapi import APIRouter, status
import logging

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.portfolio_service import PortfolioService
from ....services.unified_data_service import unified_data_service
from ..decorators import handle_portfolio_errors
from .naver_news import NaverNewsService


logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 초기화
portfolio_service = PortfolioService()
news_service = NaverNewsService()

# 통합 데이터 서비스에 뉴스 서비스 주입
unified_data_service.news_service = news_service


@router.post(
    "",
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
    - 환율 데이터 및 통계
    - 급등/급락 이벤트 & 뉴스
    - 벤치마크 데이터 (S&P 500, NASDAQ)
    
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
        "exchange_stats": {...},
        "volatility_events": { "AAPL": [...] },
        "latest_news": { "AAPL": [...] },
        "sp500_benchmark": [...],
        "nasdaq_benchmark": [...]
      }
    }
    ```
    """
    # 1. 백테스트 실행 (포트폴리오 서비스 위임)
    backtest_result = await portfolio_service.run_portfolio_backtest(request)
    
    if backtest_result.get('status') != 'success':
        return backtest_result
    
    # 2. 종목 심볼 추출 (현금 제외)
    symbols = [
        item.symbol 
        for item in request.portfolio 
        if item.symbol.upper() not in ['CASH', '현금']
    ]
    symbols = list(set(symbols))  # 중복 제거
    
    # 3. 통합 데이터 수집 (통합 데이터 서비스 위임)
    unified_data = unified_data_service.collect_all_unified_data(
        symbols=symbols,
        start_date=request.start_date,
        end_date=request.end_date,
        include_news=True,
        news_display_count=15
    )
    
    # 4. 응답 데이터 병합
    backtest_result['data'].update(unified_data)
    
    return backtest_result

