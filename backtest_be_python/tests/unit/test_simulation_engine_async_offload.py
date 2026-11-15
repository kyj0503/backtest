"""PortfolioSimulationEngine.execute_simulation / PortfolioCalculator._calculate_realistic_equity_curve
이벤트 루프 비블로킹 회귀 테스트 (P2-01)

**버그**: 두 메서드 모두 async def 이지만 내부에 await가 전혀 없다. 코루틴이 실행을
시작하면 단 한 번의 yield도 없이 전체 동기 작업(최대 10년 x N종목의 pandas/pydantic
연산)이 끝날 때까지 이벤트 루프를 독점한다. 그동안 동시에 스케줄된 다른 코루틴(다른
API 요청 처리 등)은 단 한 스텝도 진행하지 못한다.

**검증 방법**: 시뮬레이션 코루틴과, `await asyncio.sleep(0)`로 매 스텝 양보하는 카운터
코루틴을 asyncio.gather로 동시에 실행한다. asyncio.Event로 시뮬레이션 완료 시점을
표시해 두고, 카운터가 "시뮬레이션이 아직 끝나지 않은 상태에서" 몇 번이나 진행했는지를 센다.

- 버그가 있으면(동기 블로킹): 시뮬레이션 태스크가 먼저 스케줄되면 단일 스텝에서 끝까지
  실행되어 버리므로(코루틴 안에 실제 await 지점이 없어 결코 suspend되지 않는다), 카운터는
  시뮬레이션 완료 "이전"에는 단 한 번도 진행할 기회를 얻지 못한다 (진행 횟수 == 0).
- asyncio.to_thread로 워커 스레드에 위임하면: 시뮬레이션 태스크는 to_thread await
  지점에서 즉시 이벤트 루프에 제어를 반환하므로, 카운터는 백그라운드 스레드가 완료되기
  전에 최소 한 번 이상 진행할 수 있다 (진행 횟수 > 0).

이 인터리빙 판정은 실행 시간(wall-clock) 임계값에 기대지 않는다 -- asyncio.to_thread가
스레드 풀에 작업을 제출하고 그 자리에서 즉시 suspend하는 것은 타이밍이 아니라 asyncio
자체의 스케줄링 시맨틱(await 지점에서만 제어권이 넘어간다)이므로 결정적이다. 따라서
작은 데이터셋으로도 빠르고 결정적으로 검증할 수 있다.
"""
import asyncio
from datetime import datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine
from app.services.portfolio_calculator_service import portfolio_calculator

pytestmark = pytest.mark.unit


async def _count_ticks_before_event(event: asyncio.Event, iterations: int = 200) -> int:
    """event가 set되기 전까지 asyncio.sleep(0) 이후 몇 번이나 재개될 수 있었는지 센다."""
    ticks_before = 0
    for _ in range(iterations):
        if not event.is_set():
            ticks_before += 1
        await asyncio.sleep(0)
    return ticks_before


def _flat_price_frame(start: str, end: str, price: float = 100.0) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


class TestExecuteSimulationDoesNotBlockEventLoop:
    @pytest.mark.asyncio
    async def test_execute_simulation_yields_to_other_coroutines(self):
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        date_range = pd.bdate_range(start=start, end=end)

        dca_info = {
            'A': DcaStrategyInfo(
                symbol='AAA', allocation=1.0, asset_type='stock',
                investment_type='lump_sum', monthly_amount=0.0,
            ),
        }

        sim_done = asyncio.Event()

        async def run_sim():
            result = await engine.execute_simulation(
                date_range=date_range,
                start_date_obj=start,
                end_date_obj=end,
                stock_amounts={'A': 1000.0},
                amounts={'A': 1000.0},
                cash_amount=0.0,
                total_amount=1000.0,
                portfolio_data={'AAA': _flat_price_frame('2024-01-01', '2024-01-10')},
                dca_info=dca_info,
                ticker_currencies={'A': 'USD'},
                exchange_rates_by_currency={},
                rebalance_frequency='none',
                commission=0.0,
            )
            sim_done.set()
            return result

        sim_task = asyncio.create_task(run_sim())
        ticker_task = asyncio.create_task(_count_ticks_before_event(sim_done))

        result, ticks_before_done = await asyncio.wait_for(
            asyncio.gather(sim_task, ticker_task), timeout=10
        )

        assert ticks_before_done > 0, (
            "카운터 코루틴이 시뮬레이션 완료 전에 단 한 번도 진행하지 못함 -- "
            "execute_simulation이 이벤트 루프를 독점(블로킹)하고 있다는 뜻"
        )
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0


class TestCalculateRealisticEquityCurveDoesNotBlockEventLoop:
    @pytest.mark.asyncio
    async def test_calculate_realistic_equity_curve_yields_to_other_coroutines(self):
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "A", "amount": 1000.0}],
            start_date="2024-01-01",
            end_date="2024-01-05",
            strategy="sma_strategy",
        )
        equity_curve_dict = {f'2024-01-0{d}': 1000.0 + d for d in range(1, 6)}
        portfolio_results = {
            'A': {
                'amount': 1000.0,
                'final_value': 1005.0,
                'weight': 1.0,
                'strategy_stats': {'equity_curve': equity_curve_dict},
            },
        }

        calc_done = asyncio.Event()

        async def run_calc():
            result = await portfolio_calculator._calculate_realistic_equity_curve(
                request, portfolio_results, total_amount=1000.0
            )
            calc_done.set()
            return result

        calc_task = asyncio.create_task(run_calc())
        ticker_task = asyncio.create_task(_count_ticks_before_event(calc_done))

        (equity_curve, _daily_returns, _weight_history), ticks_before_done = await asyncio.wait_for(
            asyncio.gather(calc_task, ticker_task), timeout=10
        )

        assert ticks_before_done > 0, (
            "카운터 코루틴이 계산 완료 전에 단 한 번도 진행하지 못함 -- "
            "_calculate_realistic_equity_curve가 이벤트 루프를 독점(블로킹)하고 있다는 뜻"
        )
        assert len(equity_curve) == 5
