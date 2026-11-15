"""DCA 계획 회차와 실제 실행 회차의 정합성 테스트 (P1-07 / P1-08)

**배경**:
과거 구현은 백테스트 기간을 "월 = 30일" 근사로 나눠 납입 횟수를 추정하고
그 값으로 총 투자금(= 수익률의 분모)을 계산했다. 그러나 실제 매수는
Nth-weekday 달력을 따르므로 두 값이 어긋났고, 집행되지 않은 납입금이
손실처럼 보고됐다 (2024년 전체·월 $1,000·고정가 $100·수수료 0에서
실제 12회 매수인데 분모는 $13,000 → 총수익률 -7.69%).

이 테스트들은 "고정 가격·수수료 0이면 총수익률은 0%"라는 불변식을
기준으로 계획/실행 정합성을 고정한다.
"""
import pytest
import pandas as pd
from pydantic import ValidationError as PydanticValidationError
from unittest.mock import AsyncMock, patch

from datetime import datetime

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.services.rebalance_helper import generate_periodic_schedule

pytestmark = pytest.mark.unit

FLAT_PRICE = 100.0


def _flat_price_frame(start: str, end: str, price: float = FLAT_PRICE) -> pd.DataFrame:
    """영업일 기준 고정 가격 프레임 (가격이 변하지 않으므로 수익률은 0이어야 한다)."""
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _run_backtest(request: PortfolioBacktestRequest, frames: dict) -> dict:
    """stock_repository를 mock한 채 buy&hold 포트폴리오 백테스트를 실행한다."""
    import asyncio

    service = PortfolioManagerService()

    with patch.object(
        service.data_loader, 'load_stock_data_parallel', new=AsyncMock(return_value=frames)
    ), patch.object(
        service.data_loader, 'load_ticker_currencies',
        new=AsyncMock(return_value={symbol: 'USD' for symbol in frames})
    ), patch.object(
        service.data_loader, 'load_exchange_rates', new=AsyncMock(return_value={})
    ):
        return asyncio.run(service.run_buy_and_hold_portfolio_backtest(request))


def _total_return(result: dict) -> float:
    assert result['status'] == 'success', result
    return result['data']['portfolio_result']['total_return_pct']


def _final_value(result: dict) -> float:
    assert result['status'] == 'success', result
    return result['data']['portfolio_result']['total_equity']


class TestDcaDenominatorMatchesActualSchedule:
    """계획 납입 횟수가 실제 Nth-weekday 스케줄과 일치해야 한다."""

    @pytest.mark.parametrize('frequency', ['monthly_1', 'monthly_3', 'weekly_1'])
    def test_flat_price_zero_commission_dca_returns_zero_percent(self, frequency):
        """고정 가격·수수료 0인 DCA의 총수익률은 주기와 무관하게 0%여야 한다.

        수정 전에는 30일 근사로 부풀려진 분모 때문에 음수 수익률이 보고됐다
        (monthly_1 기준 -7.69%).
        """
        start, end = '2024-01-01', '2024-12-31'
        request = PortfolioBacktestRequest(
            portfolio=[{
                'symbol': 'AAPL',
                'amount': 1000.0,
                'investment_type': 'dca',
                'dca_frequency': frequency,
            }],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)

    def test_barely_longer_than_one_interval_still_returns_zero(self):
        """주기를 겨우 넘기는 짧은 기간(납입 2회)에서도 0%여야 한다.

        근사 계산의 오차가 가장 크게 드러나는 구간이다. 주기보다 더 짧은
        기간은 스키마가 이미 거부하므로(아래 별도 테스트) 여기서는 다루지 않는다.
        """
        start, end = '2024-01-01', '2024-02-20'
        request = PortfolioBacktestRequest(
            portfolio=[{
                'symbol': 'AAPL',
                'amount': 1000.0,
                'investment_type': 'dca',
                'dca_frequency': 'monthly_1',
            }],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)

    def test_period_shorter_than_dca_interval_is_rejected_by_schema(self):
        """주기보다 짧은 기간은 스키마 검증 단계에서 거부된다 (기존 동작 고정)."""
        with pytest.raises(PydanticValidationError):
            PortfolioBacktestRequest(
                portfolio=[{
                    'symbol': 'AAPL',
                    'amount': 1000.0,
                    'investment_type': 'dca',
                    'dca_frequency': 'monthly_1',
                }],
                start_date='2024-01-01',
                end_date='2024-01-15',
                commission=0.0,
                rebalance_frequency='none',
                strategy='buy_hold_strategy',
            )

    def test_lump_sum_is_unaffected(self):
        """일시불 경로는 이 변경의 영향을 받지 않아야 한다 (회귀 가드)."""
        start, end = '2024-01-01', '2024-12-31'
        request = PortfolioBacktestRequest(
            portfolio=[{
                'symbol': 'AAPL',
                'amount': 10000.0,
                'investment_type': 'lump_sum',
            }],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)
        assert _final_value(result) == pytest.approx(10000.0, abs=1e-6)


class TestPeriodicScheduleGenerator:
    """납입 예정일 생성기는 시뮬레이션과 동일한 Nth-weekday 규칙을 따라야 한다."""

    def test_monthly_full_year_yields_eleven_periodic_dates(self):
        """1년 월간 납입은 초회를 제외하고 11회다 (총 12회)."""
        dates = generate_periodic_schedule(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            period_type='monthly',
            interval=1,
        )
        assert len(dates) == 11
        assert all(datetime(2024, 1, 1) < d <= datetime(2024, 12, 31) for d in dates)
        assert dates == sorted(dates)

    def test_quarterly_full_year_yields_three_periodic_dates(self):
        dates = generate_periodic_schedule(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            period_type='monthly',
            interval=3,
        )
        assert len(dates) == 3

    def test_weekly_preserves_weekday(self):
        """주간 납입은 시작일과 같은 요일을 유지해야 한다."""
        start = datetime(2024, 3, 6)  # 수요일
        dates = generate_periodic_schedule(
            start_date=start, end_date=datetime(2024, 4, 30),
            period_type='weekly', interval=1,
        )
        assert dates
        assert all(d.weekday() == start.weekday() for d in dates)

    def test_end_before_first_interval_yields_empty(self):
        """첫 주기 도래 전에 끝나면 정기 납입은 없다 (초회만)."""
        dates = generate_periodic_schedule(
            start_date=datetime(2024, 1, 1), end_date=datetime(2024, 1, 10),
            period_type='monthly', interval=1,
        )
        assert dates == []

    def test_unknown_period_type_yields_empty(self):
        assert generate_periodic_schedule(
            datetime(2024, 1, 1), datetime(2024, 12, 31), 'daily', 1
        ) == []


class TestScheduleHoldsWithDataGaps:
    """가격 데이터에 공백이 있어도 계획 회차와 실행 회차가 일치해야 한다."""

    def test_gap_covering_a_scheduled_date_still_matches_denominator(self):
        """납입 예정일이 데이터 공백에 걸려도 총수익률은 0%여야 한다.

        시뮬레이션은 공백 다음 거래일에 해당 회차를 집행한다. 분모(계획 회차)가
        실제 스케줄에서 파생되므로 이 경우에도 어긋나지 않는다.
        """
        start, end = '2024-01-01', '2024-12-31'
        frame = _flat_price_frame(start, end)

        # 2월 납입 예정일이 포함되도록 2월 초 2주 구간의 가격을 제거한다.
        gap = (frame.index >= '2024-02-01') & (frame.index <= '2024-02-14')
        frame_with_gap = frame[~gap]

        request = PortfolioBacktestRequest(
            portfolio=[{
                'symbol': 'AAPL',
                'amount': 1000.0,
                'investment_type': 'dca',
                'dca_frequency': 'monthly_1',
            }],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(request, {'AAPL': frame_with_gap})

        # 회차가 유실되면 그만큼 분모에 못 미쳐 음수 수익률이 된다.
        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)


class TestInitialPurchaseRetriedWhenFirstDayPriceMissing:
    """첫날 가격이 없는 종목도 첫 거래 가능일에 매수되어야 한다 (P1-08)."""

    def test_asset_without_first_day_price_is_still_purchased(self):
        """한쪽 시장이 휴장인 날 시작해도 해당 종목의 자본이 증발하면 안 된다.

        수정 전에는 execute_initial_purchases가 그 종목을 건너뛴 뒤 재시도하지
        않아, 금액은 분모에 남고 포지션은 열리지 않아 수익률이 과소보고됐다.
        """
        start, end = '2024-01-01', '2024-06-30'

        # A는 전 구간 가격 존재, B는 첫 영업일 하루가 비어 있다.
        frame_a = _flat_price_frame(start, end)
        frame_b = _flat_price_frame(start, end).iloc[1:]

        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAA', 'amount': 5000.0, 'investment_type': 'lump_sum'},
                {'symbol': 'BBB', 'amount': 5000.0, 'investment_type': 'lump_sum'},
            ],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(request, {'AAA': frame_a, 'BBB': frame_b})

        # B가 매수되지 않으면 최종 평가액이 5,000에 머물러 -50%가 된다.
        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)
        assert _final_value(result) == pytest.approx(10000.0, abs=1e-6)

    def test_all_assets_priced_on_first_day_unchanged(self):
        """모든 종목이 첫날 가격을 가지면 기존과 동일하게 동작해야 한다 (회귀 가드)."""
        start, end = '2024-01-01', '2024-06-30'
        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAA', 'amount': 5000.0, 'investment_type': 'lump_sum'},
                {'symbol': 'BBB', 'amount': 5000.0, 'investment_type': 'lump_sum'},
            ],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_backtest(
            request,
            {'AAA': _flat_price_frame(start, end), 'BBB': _flat_price_frame(start, end)},
        )

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)
        assert _final_value(result) == pytest.approx(10000.0, abs=1e-6)
