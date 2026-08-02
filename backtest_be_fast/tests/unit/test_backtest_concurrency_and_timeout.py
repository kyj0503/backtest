"""
POST /api/v1/backtest 동시 실행 제한 및 타임아웃(P2-16) 회귀 테스트

**배경**:
POST /api/v1/backtest는 동시 실행 제한도, 요청당 시간 제한도 없었다. 포트폴리오
크기는 settings.max_portfolio_items로 제한되지만 "동시 요청 수 x 기간 x 종목 수"로
늘어나는 총 작업량에는 상한이 없다. 이미 다른 배치가 CPU 무거운 시뮬레이션을
asyncio.to_thread로 워커 스레드에 위임했으므로(portfolio_simulation_engine.py::
execute_simulation), 이벤트 루프 블로킹이 아니라 "프로세스 공유 스레드풀 고갈"이
남은 위험이다: 동시 요청이 많으면 스레드풀 슬롯을 오래 점유해 다른 요청(및 다른
엔드포인트)까지 밀릴 수 있다.

**수정**: app/api/v1/endpoints/backtest.py에
- `_backtest_semaphore`(asyncio.Semaphore, 크기는 MAX_CONCURRENT_BACKTESTS)로
  "실제로 계산 중인" 요청 수를 제한한다. 초과 요청은 거부되지 않고 세마포어에서
  대기(큐잉)한다.
- 세마포어 획득 대기 + 실제 실행을 합쳐 BACKTEST_TIMEOUT_SECONDS로 전체 시간을
  제한한다 (asyncio.wait_for). 시간 초과 시 예외를 그냥 던지지 않고 JSONResponse를
  직접 반환해 @handle_portfolio_errors의 catch-all(500)을 우회하고 504를 유지한다
  -- HTTPException을 직접 raise하면 handle_portfolio_errors가 알지 못하는 예외
  타입이라 500으로 뭉개진다.
두 상수 모두 os.getenv()로 오버라이드 가능하다 (app/core/config.py는 이번 배치의
수정 대상 파일 목록에 없어 손댈 수 없었다 -- Settings 클래스에 필드를 추가하는
대신 이 방식을 선택했다).

이 파일의 두 테스트는 프로덕션 기본값에 의존하지 않도록 monkeypatch로 세마포어
크기/타임아웃 값을 테스트 전용의 작은 값으로 바꿔서 빠르고 결정적으로 검증한다.
"""
import asyncio
import time

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

import app.api.v1.endpoints.backtest as backtest_module
from app.main import app
from app.schemas.schemas import PortfolioBacktestRequest

pytestmark = pytest.mark.unit

client = TestClient(app)


def _mock_stock_repository() -> MagicMock:
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


def _valid_request() -> PortfolioBacktestRequest:
    return PortfolioBacktestRequest(
        portfolio=[{"symbol": "AAPL", "amount": 10000.0}],
        start_date="2023-01-01",
        end_date="2023-06-30",
        strategy="buy_hold_strategy",
    )


class TestConcurrentBacktestsAreBounded:
    @pytest.mark.asyncio
    async def test_concurrent_requests_never_exceed_the_configured_cap(self, monkeypatch):
        """RED(수정 전): _backtest_semaphore가 존재하지 않아(또는 참조되지 않아)
        동시 요청 수를 전혀 제한하지 못한다 -- 5개를 동시에 보내면 5개 모두
        동시에 "실행 중" 상태가 된다 (peak == 5), cap(2)을 넘어선다."""
        cap = 2
        monkeypatch.setattr(backtest_module, "_backtest_semaphore", asyncio.Semaphore(cap), raising=False)
        # 타임아웃 때문에 조기 종료되지 않도록 충분히 크게 잡는다
        monkeypatch.setattr(backtest_module, "BACKTEST_TIMEOUT_SECONDS", 10.0, raising=False)

        state = {"current": 0, "peak": 0}

        async def tracked_backtest(*args, **kwargs):
            state["current"] += 1
            state["peak"] = max(state["peak"], state["current"])
            await asyncio.sleep(0.08)
            state["current"] -= 1
            return {
                "status": "success",
                "data": {"portfolio_statistics": {}, "individual_returns": {}},
            }

        unified_data = {
            "sp500_benchmark": [],
            "nasdaq_benchmark": [],
            "exchange_rates": {},
            "latest_news": [],
        }

        total_requests = 5
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=_mock_stock_repository(),
        ), patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(side_effect=tracked_backtest),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value=unified_data,
        ):
            results = await asyncio.gather(
                *[backtest_module.run_portfolio_backtest(_valid_request()) for _ in range(total_requests)]
            )

        assert len(results) == total_requests
        assert state["peak"] <= cap, (
            f"동시 실행 최대치({state['peak']})가 설정된 상한({cap})을 초과함 -- "
            "세마포어가 동시 실행 수를 제한하지 못하고 있다는 뜻"
        )
        assert state["peak"] == cap, (
            f"세마포어가 지나치게 보수적으로 동작함: peak={state['peak']}, cap={cap} "
            "(최소한 cap만큼은 동시에 실행되어야 한다)"
        )


class TestOverLongBacktestIsTerminatedWithProperStatusCode:
    def test_backtest_exceeding_timeout_returns_504_quickly(self, monkeypatch):
        """RED(수정 전): BACKTEST_TIMEOUT_SECONDS가 존재하지 않아(또는 참조되지
        않아) 요청이 서비스 계층의 응답을 그대로 기다린다 -- 목(mock)이 0.3초
        걸리면 요청도 0.3초 넘게 걸리고 200을 반환한다. 수정 후에는 타임아웃
        (0.05초)이 먼저 발동해 504를 빠르게 반환해야 한다."""
        monkeypatch.setattr(backtest_module, "BACKTEST_TIMEOUT_SECONDS", 0.05, raising=False)
        # 세마포어가 이 단일 요청을 막지 않도록 넉넉하게 잡는다
        monkeypatch.setattr(backtest_module, "_backtest_semaphore", asyncio.Semaphore(4), raising=False)

        async def slow_backtest(*args, **kwargs):
            await asyncio.sleep(0.3)
            return {
                "status": "success",
                "data": {"portfolio_statistics": {}, "individual_returns": {}},
            }

        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
        }

        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=_mock_stock_repository(),
        ), patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(side_effect=slow_backtest),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value={
                "sp500_benchmark": [],
                "nasdaq_benchmark": [],
                "exchange_rates": {},
                "latest_news": [],
            },
        ):
            start = time.monotonic()
            response = client.post("/api/v1/backtest", json=payload)
            elapsed = time.monotonic() - start

        assert response.status_code == 504, (
            f"타임아웃을 초과한 요청이 504가 아닌 {response.status_code}로 응답함: "
            f"{response.text}"
        )
        assert elapsed < 0.2, (
            f"타임아웃(0.05초)이 아니라 목(mock)의 전체 sleep(0.3초)을 그대로 "
            f"기다린 것으로 보임: 실제 소요 {elapsed:.3f}초"
        )
        assert response.json().get("detail"), "타임아웃 응답에 detail 메시지가 없음"
