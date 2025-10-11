"""
백테스팅 API 엔드포인트

**역할**:
- FastAPI 라우터로 백테스트 관련 HTTP 엔드포인트 제공
- 요청 검증 및 응답 반환만 수행 (Controller 역할)
- 비즈니스 로직은 서비스 레이어에 위임

**엔드포인트**:
- POST /api/v1/backtest: 백테스트 실행 및 모든 데이터 반환

**요청 흐름**:
1. 클라이언트 → FastAPI → 이 엔드포인트
2. 요청 검증 (Pydantic 모델)
3. 서비스 레이어 호출
4. 응답 직렬화 및 반환

**에러 처리**:
- @handle_portfolio_errors 데코레이터로 일관된 에러 응답

**의존성**:
- app/services/portfolio_service.py: 백테스트 실행
- app/services/unified_data_service.py: 추가 데이터 수집
- app/services/news_service.py: 뉴스 데이터 조회

**연관 컴포넌트**:
- Backend: app/api/v1/api.py (라우터 등록)
- Backend: app/schemas/schemas.py (요청/응답 스키마)
- Frontend: src/features/backtest/api/backtestService.ts (API 클라이언트)

**아키텍처 패턴**:
- Controller-Service-Repository 패턴
- 얇은 컨트롤러: 비즈니스 로직 없이 조율만 수행
"""
from fastapi import APIRouter, status
import logging

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.portfolio_service import PortfolioService
from ....services.unified_data_service import unified_data_service
from ....services.news_service import news_service
from ..decorators import handle_portfolio_errors


logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 초기화
portfolio_service = PortfolioService()

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

