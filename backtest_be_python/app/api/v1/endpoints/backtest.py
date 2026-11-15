"""백테스팅 API 엔드포인트

POST /api/v1/backtest: 포트폴리오 백테스트를 실행하고 결과와 부가 데이터(include_*)를 반환한다.

계산 계약·응답 스키마는 운영 기준인 Go 백엔드와 같다(app/engine 참고). 요청 형태 검증은
PortfolioBacktestRequest(pydantic 422 목록), 업무 규칙은 app/engine/request.py(422 문자열)가 한다.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
import logging
from typing import Optional

from ....schemas.schemas import PortfolioBacktestRequest
from ....services.unified_data_service import unified_data_service
from ....services.news_service import news_service
from ....core.config import settings
from ....core.client_ip import client_limit_key, parse_trusted_networks, resolve_client_ip
from ....engine import service as engine_service
from ....engine.request import Request as EngineRequest
from ....services.backtest_runner import BacktestRejected, get_backtest_runner
from ..decorators import handle_portfolio_errors
from ..turnstile import require_turnstile

logger = logging.getLogger(__name__)
router = APIRouter()

# 데이터 서비스에 뉴스 서비스 주입 (부가 데이터 news 섹션이 쓴다)
unified_data_service.news_service = news_service

# --- [P2-04] 포트폴리오 백테스트 최소 기간 ---
# 스키마가 아니라 엔드포인트(engine_service.to_request)에서 강제한다.
MIN_BACKTEST_PERIOD_DAYS = settings.min_backtest_period_days

# --- 동시 실행 상한 · 타임아웃 · 취소 · IP별 상한 (P2-16 → A-04/A-05/A-06) ---
# app/services/backtest_runner.py가 처리한다(설계와 한계는 그 모듈 docstring).
_trusted_proxies = parse_trusted_networks(settings.trusted_proxy_cidrs)


async def _execute_portfolio_backtest(req: EngineRequest):
    """백테스트 실행 본체: 시세 로드 → 계산 → 부가 데이터.

    backtest_runner가 동시 실행 슬롯을 얻은 뒤 작업 전용 스레드·이벤트 루프에서 실행한다. 업무 규칙
    검증(최소 기간 포함)은 슬롯을 잡기 전에 끝나 있다(거부될 요청이 슬롯을 점유하지 않도록).
    """
    return engine_service.compute(req)


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
    dependencies=[Depends(require_turnstile)],
    responses={
        403: {"description": "사람 인증 누락·실패·만료 또는 토큰 재사용 — 계산을 시작하지 않음"},
        429: {"description": "같은 클라이언트(IP)의 동시 실행 상한 초과 — 대기 없이 즉시 거부"},
        503: {"description": "사람 인증 검증 불가 또는 동시 실행 슬롯 대기 시간 초과 — 작업을 시작하지 않음"},
        504: {"description": "실행 시간 초과 — 작업에 취소 신호를 보냄"},
    },
)
@handle_portfolio_errors
async def run_portfolio_backtest(request: PortfolioBacktestRequest, http_request: Request):
    """포트폴리오 백테스트 실행 및 주가, 환율, 뉴스, 벤치마크 데이터 반환"""
    req = engine_service.to_request(request)

    # 거부(429)·대기 초과(503)·실행 시간 초과(504)는 예외를 raise하지 않고
    # JSONResponse를 return한다. 작업 안에서 난 예외(AppError 등)는 runner가 그대로
    # 다시 던지므로 데코레이터가 상태 코드로 매핑한다.
    symbols = [a.symbol for a in req.portfolio]
    try:
        return await get_backtest_runner().run(
            lambda: _execute_portfolio_backtest(req),
            client_key=_client_key(http_request),
            is_disconnected=http_request.is_disconnected,
            label=",".join(symbols)[:200],
        )
    except BacktestRejected as exc:
        logger.warning(f"백테스트 거부/중단 ({exc.status_code}): {symbols} - {exc.detail}")
        return _rejection_response(exc)
