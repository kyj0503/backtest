"""백테스팅 API 엔드포인트

포트폴리오 백테스트 실행 및 관련 데이터를 반환하는 FastAPI 엔드포인트입니다.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import logging
import asyncio
import os
from datetime import datetime

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.portfolio_manager_service import portfolio_manager_service
from ....repositories.stock_repository import get_stock_repository
from ....services.unified_data_service import unified_data_service
from ....services.news_service import news_service
from ....core.exceptions import ValidationError
from ..decorators import handle_portfolio_errors

logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 초기화 (임포트됨)

# 데이터 서비스에 뉴스 서비스 주입
unified_data_service.news_service = news_service

# --- [P2-04] 포트폴리오 백테스트 최소 기간 ---
# app/schemas/schemas.py가 아니라 여기서 강제하는 이유: PortfolioBacktestRequest를
# 직접 생성해 DCA/리밸런싱/시뮬레이션 엔진만 단위테스트하는 기존 테스트들
# (예: tests/unit/test_dca_schedule_alignment.py, test_portfolio_manager_batch4_fixes.py,
# test_portfolio_calculator_equity_curve.py, test_simulation_engine_async_offload.py)이
# 3~14일짜리 짧은 기간을 사용한다. 스키마 레벨에 30일 하한을 넣으면 그 테스트들이
# 전부 깨진다. 실제 HTTP 요청만 거치는 엔드포인트 레벨에 두면 그 테스트들에는
# 영향을 주지 않으면서 실제 사용자 요청은 여전히 막을 수 있다.
MIN_BACKTEST_PERIOD_DAYS = 30

# --- [P2-16] 동시 실행 제한 & 타임아웃 ---
# 포트폴리오 크기는 settings.max_portfolio_items로 제한되지만 "동시 요청 수 x
# 기간 x 종목 수"로 늘어나는 총 작업량에는 상한이 없다. 다른 배치가 CPU 무거운
# 시뮬레이션을 asyncio.to_thread로 워커 스레드에 위임했으므로(portfolio_
# simulation_engine.py::execute_simulation) 이벤트 루프 블로킹은 이미 해소됐고,
# 남은 위험은 "프로세스 공유 스레드풀(기본 min(32, cpu+4)개) 고갈"이다 -- 동시
# 요청이 많으면 스레드풀 슬롯을 오래 점유해 다른 요청(및 다른 엔드포인트)까지
# 밀릴 수 있다.
#
# app/core/config.py(Settings)는 이번 배치의 수정 대상 파일 목록에 없어 손댈 수
# 없었다. 대신 os.getenv()로 오버라이드 가능한 모듈 상수로 구성했다 -- 여전히
# "configurable"하다는 요구를 만족하면서 파일 범위를 지킨다.
MAX_CONCURRENT_BACKTESTS = int(os.getenv("MAX_CONCURRENT_BACKTESTS", "8"))
BACKTEST_TIMEOUT_SECONDS = float(os.getenv("BACKTEST_TIMEOUT_SECONDS", "60"))
# 세마포어는 모듈 임포트 시점의 MAX_CONCURRENT_BACKTESTS 값으로 크기가 고정된다
# (asyncio.Semaphore는 동적으로 리사이즈할 수 없음). 테스트는 이 객체 자체를
# monkeypatch로 교체해 작은 값으로 검증한다.
_backtest_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BACKTESTS)


async def _execute_portfolio_backtest(request: PortfolioBacktestRequest) -> dict:
    """포트폴리오 백테스트 실행 본체 (주가/환율/뉴스/벤치마크 데이터 포함).

    _backtest_semaphore + asyncio.wait_for(BACKTEST_TIMEOUT_SECONDS) 안에서
    실행되는 실제 작업. 최소 기간 검증(MIN_BACKTEST_PERIOD_DAYS)은 이 함수
    호출 전, 세마포어를 잡기도 전에 끝나 있어야 한다 (거부될 요청이 동시 실행
    슬롯을 점유하지 않도록).
    """
    # P2-09: 현금 자산은 symbol 문자열이 아니라 asset_type으로 판별한다.
    # symbol.upper() not in ['CASH', '현금'] 방식은 asset_type='cash'인데
    # 커스텀 이름(예: "예금")을 쓰는 항목을 걸러내지 못해, 실재하지 않는
    # "티커"가 상장일 조회/yfinance 조회(재시도 sleep 포함)까지 흘러들어갔다.
    symbols = [
        item.symbol
        for item in request.portfolio
        if item.asset_type != 'cash'
    ]
    symbols = list(set(symbols))  # 중복 제거

    # 종목 정보 조회 (상장일 확인용) - 배치 조회로 최적화 (N+1 쿼리 → 1개 쿼리)
    ticker_info_dict = await asyncio.to_thread(
        get_stock_repository().get_tickers_info_batch, symbols
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
    # 실패는 예외로 전파되어 @handle_portfolio_errors가 처리하므로,
    # 이 지점에 도달했다면 항상 성공 결과다.
    backtest_result = await portfolio_manager_service.run_portfolio_backtest(request)

    # 3. 추가 데이터 수집 (데이터 서비스 위임) — asyncio.to_thread로 이벤트 루프 블로킹 방지
    unified_data = await asyncio.to_thread(
        unified_data_service.collect_all_unified_data,
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


async def _acquire_and_execute(request: PortfolioBacktestRequest) -> dict:
    """동시 실행 한도(_backtest_semaphore) 안에서 실제 백테스트를 실행한다.

    한도를 초과한 요청은 거부되지 않고 세마포어 대기열에서 큐잉된다 (P2-16).
    """
    async with _backtest_semaphore:
        return await _execute_portfolio_backtest(request)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행",
    description="포트폴리오 백테스트 실행 및 관련 데이터 반환"
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest):
    """포트폴리오 백테스트 실행 및 주가, 환율, 뉴스, 벤치마크 데이터 반환"""
    start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d').date()
    period_days = (end_date_obj - start_date_obj).days
    if period_days < MIN_BACKTEST_PERIOD_DAYS:
        raise ValidationError(
            f"백테스트 기간이 너무 짧습니다: {period_days}일 "
            f"(최소 {MIN_BACKTEST_PERIOD_DAYS}일 필요)"
        )

    # [P2-16] 동시 실행 제한(세마포어 대기 포함) + 전체 처리 시간 상한.
    # asyncio.TimeoutError를 여기서 잡아 JSONResponse를 직접 반환하는 이유:
    # HTTPException을 raise하면 @handle_portfolio_errors의 wrapper가 알고 있는
    # 예외 타입(ValidationError/DataNotFoundError/InvalidSymbolError/
    # YfinanceRateLimitError)이 아니라서 catch-all에 걸려 500으로 뭉개진다.
    # Response 객체를 직접 반환하면(=raise가 아니라 return) 데코레이터의
    # try/except를 그대로 통과하므로 504 상태 코드가 유지된다.
    try:
        return await asyncio.wait_for(
            _acquire_and_execute(request),
            timeout=BACKTEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.error(
            f"백테스트 처리 시간 초과 ({BACKTEST_TIMEOUT_SECONDS}초): "
            f"{[item.symbol for item in request.portfolio]}"
        )
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content={
                "detail": (
                    f"백테스트 처리 시간이 {BACKTEST_TIMEOUT_SECONDS:.0f}초를 초과하여 "
                    "중단되었습니다. 기간을 줄이거나 잠시 후 다시 시도해주세요."
                )
            },
            headers={"Retry-After": "30"},
        )

