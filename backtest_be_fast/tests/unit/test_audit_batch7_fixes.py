"""배치7 수정 회귀 테스트: DCA 낙폭(MDD), 전략×DCA/리밸런싱 거부(A-02),
데이터 로드 실패 종목의 무경고 원금 증발(A-03)

세 건 모두 수정 전에는 HTTP 200 + status=success로 **틀린 숫자**가 나가던
문제라 게이트가 잡지 못했다. 각 테스트는 수정 전 코드에서 실패한다.
"""
import asyncio
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.utils.metrics_math import drawdown_from_returns

pytestmark = pytest.mark.unit

START, END = '2022-01-03', '2023-12-29'


def _declining_frame(start: str = START, end: str = END, first: float = 100.0, last: float = 60.0) -> pd.DataFrame:
    """영업일마다 같은 폭으로 first → last까지 하락하는 가격 프레임."""
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': np.linspace(first, last, len(index))}, index=index)


def _flat_frame(price: float = 100.0, start: str = START, end: str = END) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _run_buy_hold(request: PortfolioBacktestRequest, frames: dict) -> dict:
    """stock_repository를 mock한 채 buy&hold 경로를 실행한다.

    frames에 없는 종목은 data_loader가 로드 실패로 버린 것과 같은 상태가 된다.
    """
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


def _request(portfolio, **overrides) -> PortfolioBacktestRequest:
    params = dict(
        portfolio=portfolio,
        start_date=START,
        end_date=END,
        commission=0.0,
        rebalance_frequency='none',
        strategy='buy_hold_strategy',
    )
    params.update(overrides)
    return PortfolioBacktestRequest(**params)


class TestDrawdownIgnoresDcaInflows:
    """낙폭은 납입금이 아니라 가격 변동만 반영해야 한다."""

    def test_helper_does_not_let_inflows_hide_a_decline(self):
        """평가금 100 → 90(-10%) 다음 날 50을 납입해 140이 돼도, 가격 기준으로는
        여전히 -10% 구간이다. 평가금으로 재면 둘째 날부터 신고점이라 낙폭이 사라진다.
        """
        # Daily_Return은 납입금을 뺀 값: (140 - 90 - 50) / 90 = 0
        returns = pd.Series([0.0, -0.10, 0.0, 0.0])
        drawdown = drawdown_from_returns(returns)

        assert drawdown.min() == pytest.approx(-10.0)
        assert drawdown.tolist() == pytest.approx([0.0, -10.0, -10.0, -10.0])

    def test_helper_treats_full_recovery_float_noise_as_zero(self):
        """-5% 후 정확히 회복한 날은 누적곱 오차가 있어도 낙폭일로 세지 않는다."""
        returns = pd.Series([0.0, -0.05, 1 / 0.95 - 1, -0.15, 1 / 0.85 - 1])
        drawdown = drawdown_from_returns(returns)

        assert (drawdown < 0).sum() == 2
        assert drawdown[drawdown < 0].mean() == pytest.approx(-10.0)

    def test_dca_into_steadily_falling_stock_reports_the_real_drawdown(self):
        """2년간 100 → 60(-40%)으로 꾸준히 하락하는 종목에 매월 적립.

        수정 전: 매달 납입금이 평가금을 신고점으로 밀어 올려 MDD가 -2.85%로
        보고됐다(총수익률은 -24%인데). 항상 전액 투자 상태이므로 가격 기준
        낙폭은 일시금과 같은 -40%다.
        """
        request = _request([{
            'symbol': 'AAPL', 'amount': 1000.0,
            'investment_type': 'dca', 'dca_frequency': 'monthly_1',
        }])
        result = _run_buy_hold(request, {'AAPL': _declining_frame()})

        assert result['status'] == 'success', result
        stats = result['data']['portfolio_statistics']
        assert stats['Max_Drawdown'] == pytest.approx(-40.0, abs=0.5)

    def test_lump_sum_drawdown_is_unchanged(self):
        """납입이 없으면 시간가중 지수와 평가금이 비례하므로 결과가 같아야 한다."""
        request = _request([{'symbol': 'AAPL', 'amount': 1000.0}])
        result = _run_buy_hold(request, {'AAPL': _declining_frame()})

        stats = result['data']['portfolio_statistics']
        assert stats['Max_Drawdown'] == pytest.approx(-40.0, abs=1e-6)
        assert stats['Total_Return'] == pytest.approx(-40.0, abs=1e-6)


class TestStrategyRejectsDcaAndRebalancing:
    """A-02: 전략 경로는 DCA·리밸런싱을 구현하지 않으므로 조용히 무시하지 말고 거부한다."""

    def test_technical_strategy_with_dca_is_rejected(self):
        with pytest.raises(PydanticValidationError, match='분할 매수'):
            _request(
                [{'symbol': 'AAPL', 'amount': 500.0, 'investment_type': 'dca', 'dca_frequency': 'monthly_1'}],
                strategy='sma_strategy',
            )

    def test_technical_strategy_with_explicit_rebalancing_is_rejected(self):
        with pytest.raises(PydanticValidationError, match='리밸런싱'):
            _request(
                [{'symbol': 'AAPL', 'amount': 500.0}, {'symbol': 'MSFT', 'amount': 500.0}],
                strategy='rsi_strategy',
                rebalance_frequency='monthly_3',
            )

    def test_technical_strategy_without_rebalance_field_is_still_accepted(self):
        """필드를 생략한 기존 호출은 기본값('monthly_1') 때문에 깨지면 안 된다."""
        request = PortfolioBacktestRequest(
            portfolio=[{'symbol': 'AAPL', 'amount': 500.0}],
            start_date=START,
            end_date=END,
            strategy='sma_strategy',
        )
        assert request.strategy == 'sma_strategy'

    def test_technical_strategy_with_lump_sum_and_no_rebalancing_is_accepted(self):
        request = _request([{'symbol': 'AAPL', 'amount': 500.0}], strategy='macd_strategy')
        assert request.rebalance_frequency == 'none'

    def test_buy_hold_keeps_supporting_dca_and_rebalancing(self):
        request = _request(
            [
                {'symbol': 'AAPL', 'amount': 500.0, 'investment_type': 'dca', 'dca_frequency': 'monthly_1'},
                {'symbol': 'MSFT', 'amount': 500.0},
            ],
            rebalance_frequency='monthly_3',
        )
        assert request.strategy == 'buy_hold_strategy'


class TestFailedSymbolIsExcludedWithWarning:
    """A-03: 로드 실패 종목의 금액이 분모에 남아 수익률이 과소보고되면 안 된다."""

    def test_failed_symbol_is_excluded_from_denominator_and_warned(self):
        """AAPL(-40%)만 로드되고 ZZZZ는 실패. 수정 전에는 분모가 두 종목 합계라
        -20%로 보고되고 경고도 없었다. 나머지 종목만으로 계산한 -40%와 같아야 한다.
        """
        request = _request([
            {'symbol': 'AAPL', 'amount': 1000.0},
            {'symbol': 'ZZZZ', 'amount': 1000.0},
        ])
        result = _run_buy_hold(request, {'AAPL': _declining_frame()})

        assert result['status'] == 'success', result
        data = result['data']
        assert data['portfolio_statistics']['Total_Return'] == pytest.approx(-40.0, abs=1e-6)
        assert data['portfolio_statistics']['Initial_Value'] == pytest.approx(1000.0)
        assert len(data['warnings']) == 1
        assert 'ZZZZ' in data['warnings'][0]
        assert [c['symbol'] for c in data['portfolio_composition']] == ['AAPL']

    def test_all_stocks_failing_with_cash_warns_instead_of_reporting_silent_zero(self):
        """주식이 전부 실패하고 현금만 남으면 현금 전용 결과가 나가되, 경고가 있어야 한다."""
        request = _request([
            {'symbol': 'ZZZZ', 'amount': 1000.0},
            {'symbol': 'CASH', 'amount': 1000.0, 'asset_type': 'cash'},
        ])
        result = _run_buy_hold(request, {})

        assert result['status'] == 'success', result
        assert any('ZZZZ' in w for w in result['data']['warnings'])
        assert result['data']['portfolio_statistics']['Initial_Value'] == pytest.approx(1000.0)

    def test_successful_run_always_carries_an_empty_warnings_list(self):
        """buy&hold 응답에도 전략 경로와 같은 warnings 키가 항상 있어야 한다."""
        request = _request([{'symbol': 'AAPL', 'amount': 1000.0}])
        result = _run_buy_hold(request, {'AAPL': _flat_frame()})

        assert result['data']['warnings'] == []
