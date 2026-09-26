"""백테스팅 API 엔드포인트

포트폴리오 백테스트 실행 및 관련 데이터를 반환하는 FastAPI 엔드포인트입니다.
"""

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
import logging
import asyncio
from datetime import datetime
from typing import Optional

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.portfolio_manager_service import portfolio_manager_service
from ....repositories.stock_repository import get_stock_repository
from ....services.unified_data_service import unified_data_service
from ....services.news_service import news_service
from ....core.config import settings
from ....core.exceptions import ValidationError
from ....core.client_ip import client_limit_key, parse_trusted_networks, resolve_client_ip
from ....services.backtest_runner import BacktestRejected, get_backtest_runner
from ..decorators import handle_portfolio_errors

logger = logging.getLogger(__name__)
router = APIRouter()

# 서비스 초기화 (임포트됨)

# 데이터 서비스에 뉴스 서비스 주입
unified_data_service.news_service = news_service

# --- [P2-04] 포트폴리오 백테스트 최소 기간 ---
# 스키마가 아니라 엔드포인트에서 강제한다. 스키마는 "요청 데이터의 형태"를,
# 엔드포인트는 "HTTP 요청으로 받아들일 정책"을 책임진다 — 시뮬레이션 엔진을
# 직접 호출하는 내부 사용(단위 테스트 포함)에는 이 하한이 적용되지 않는 것이
# 의도된 동작이다.
MIN_BACKTEST_PERIOD_DAYS = settings.min_backtest_period_days

# --- 동시 실행 상한 · 타임아웃 · 취소 · IP별 상한 (P2-16 → A-04/A-05/A-06) ---
# 슬롯 대기, 실행 시간 상한, 취소 전파, IP별 상한은 모두
# app/services/backtest_runner.py가 처리한다(설계와 한계는 그 모듈 docstring).
# 값은 Settings(max_concurrent_backtests, backtest_timeout_seconds,
# backtest_queue_timeout_seconds, max_concurrent_backtests_per_client 등)에서 읽는다.
_trusted_proxies = parse_trusted_networks(settings.trusted_proxy_cidrs)


async def _execute_portfolio_backtest(request: PortfolioBacktestRequest) -> dict:
    """포트폴리오 백테스트 실행 본체 (주가/환율/뉴스/벤치마크 데이터 포함).

    backtest_runner가 동시 실행 슬롯을 얻은 뒤 작업 전용 스레드·이벤트 루프에서
    실행하는 실제 작업. 최소 기간 검증(MIN_BACKTEST_PERIOD_DAYS)은 이 함수
    호출 전, 슬롯을 잡기도 전에 끝나 있어야 한다 (거부될 요청이 동시 실행
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


def _client_key(http_request: Request) -> Optional[str]:
    """IP별 동시 실행 상한에 쓸 클라이언트 키. 식별할 수 없으면 None(제한 미적용)."""
    peer = http_request.client.host if http_request.client else None
    client_ip = resolve_client_ip(
        peer, http_request.headers.getlist("x-forwarded-for"), _trusted_proxies
    )
    return client_limit_key(client_ip)


def _rejection_response(exc: BacktestRejected) -> JSONResponse:
    headers = {"Retry-After": str(exc.retry_after)} if exc.retry_after else None
    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="포트폴리오 백테스트 실행",
    description="포트폴리오 백테스트 실행 및 관련 데이터 반환",
    responses={
        429: {"description": "같은 클라이언트(IP)의 동시 실행 상한 초과 — 대기 없이 즉시 거부"},
        503: {"description": "동시 실행 슬롯 대기 시간 초과 — 작업을 시작하지 않음"},
        504: {"description": "실행 시간 초과 — 작업에 취소 신호를 보냄"},
    },
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest, http_request: Request):
    """포트폴리오 백테스트 실행 및 주가, 환율, 뉴스, 벤치마크 데이터 반환"""
    start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d').date()
    end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d').date()
    period_days = (end_date_obj - start_date_obj).days
    if period_days < MIN_BACKTEST_PERIOD_DAYS:
        raise ValidationError(
            f"백테스트 기간이 너무 짧습니다: {period_days}일 "
            f"(최소 {MIN_BACKTEST_PERIOD_DAYS}일 필요)"
        )

    # 거부(429)·대기 초과(503)·실행 시간 초과(504)는 예외를 raise하지 않고
    # JSONResponse를 return한다. HTTPException을 raise하면 @handle_portfolio_errors의
    # catch-all에 걸려 500으로 뭉개진다(P2-16). 작업 안에서 난 예외
    # (ValidationError, DataNotFoundError 등)는 runner가 그대로 다시 던지므로
    # 기존처럼 데코레이터가 상태 코드로 매핑한다.
    symbols = [item.symbol for item in request.portfolio]
    try:
        return await get_backtest_runner().run(
            lambda: _execute_portfolio_backtest(request),
            client_key=_client_key(http_request),
            is_disconnected=http_request.is_disconnected,
            label=",".join(symbols)[:200],
        )
    except BacktestRejected as exc:
        logger.warning(f"백테스트 거부/중단 ({exc.status_code}): {symbols} - {exc.detail}")
        return _rejection_response(exc)

