"""백테스팅 API 엔드포인트

포트폴리오 백테스트 실행 및 관련 데이터를 반환하는 FastAPI 엔드포인트입니다.
"""
from fastapi import APIRouter, status
import logging
import asyncio
from datetime import datetime

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.portfolio_service import PortfolioService
from ....services.yfinance_db import get_ticker_info_batch_from_db
from ....services.unified_data_service import unified_data_service
from ....services.news_service import news_service
from ....core.exceptions import ValidationError
from ..decorators import handle_portfolio_errors


logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 초기화
portfolio_service = PortfolioService()

# 데이터 서비스에 뉴스 서비스 주입
unified_data_service.news_service = news_service


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행",
    description="포트폴리오 백테스트 실행 및 관련 데이터 반환"
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """포트폴리오 백테스트 실행 및 주가, 환율, 뉴스, 벤치마크 데이터 반환"""
    symbols = [
        item.symbol 
        for item in request.portfolio 
        if item.symbol.upper() not in ['CASH', '현금']
    ]
    symbols = list(set(symbols))  # 중복 제거

    # 종목 정보 조회 (상장일 확인용) - 배치 조회로 최적화 (N개 쿼리 → 1개 쿼리)
    ticker_info_dict = await asyncio.to_thread(
        get_ticker_info_batch_from_db, symbols
    )

    validation_errors = []

    for symbol in symbols:
        ticker_info = ticker_info_dict.get(symbol, {})
        first_trade_date_str = ticker_info.get('first_trade_date')
        
        if first_trade_date_str:
            # 날짜 문자열을 date 객체로 변환하여 안전하게 비교
            listing_date = datetime.strptime(first_trade_date_str, '%Y-%m-%d').date()
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
            
            if listing_date > start_date:
                company_name = ticker_info.get('company_name', symbol)
                validation_errors.append(
                    f"{company_name}({symbol})는 {first_trade_date_str}에 상장했습니다. "
                    f"백테스트 시작일({request.start_date})을 {first_trade_date_str} 이후로 변경해주세요."
                )
    
    # 상장일 검증 실패 시 오류 반환
    if validation_errors:
        logger.error(f"상장일 검증 실패: {validation_errors}")
        raise ValidationError(
            "포트폴리오에 백테스트 시작일 이후에 상장한 종목이 포함되어 있습니다.\n\n" + 
            "\n".join(f"• {err}" for err in validation_errors)
        )
    
    # 2. 백테스트 실행 (포트폴리오 서비스 위임)
    backtest_result = await portfolio_service.run_portfolio_backtest(request)
    
    if backtest_result.get('status') != 'success':
        return backtest_result
    
    # 3. 추가 데이터 수집 (데이터 서비스 위임)
    unified_data = unified_data_service.collect_all_unified_data(
        symbols=symbols,
        start_date=request.start_date,
        end_date=request.end_date,
        include_news=True,
        news_display_count=15
    )

    # 4. S&P 500 벤치마크 통계 계산 및 추가
    sp500_benchmark = unified_data.get('sp500_benchmark', [])
    if sp500_benchmark and len(sp500_benchmark) > 0:
        # S&P 500 수익률 계산
        sp500_return = unified_data_service.calculate_benchmark_return(sp500_benchmark)

        # 포트폴리오 통계에 추가
        portfolio_stats = backtest_result['data'].get('portfolio_statistics', {})
        if portfolio_stats:
            portfolio_stats['sp500_total_return_pct'] = sp500_return

            # 전략 수익률과 S&P 500 수익률 비교 (알파)
            strategy_return = portfolio_stats.get('Total_Return', 0.0)
            portfolio_stats['alpha_vs_sp500_pct'] = strategy_return - sp500_return

            logger.info(f"S&P 500 수익률: {sp500_return:.2f}%, 알파: {strategy_return - sp500_return:.2f}%")

    # 5. 응답 데이터 병합
    backtest_result['data'].update(unified_data)

    return backtest_result

