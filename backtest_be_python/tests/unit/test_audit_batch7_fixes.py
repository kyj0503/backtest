"""A-02: 기술 전략에 DCA·리밸런싱을 함께 요청하면 스키마가 거부한다.

계산 관련 회귀(DCA 낙폭, 실패 종목 제외·경고)는 tests/unit/test_engine_*.py가 다룬다.
"""
import pytest
from pydantic import ValidationError as PydanticValidationError

from app.schemas.schemas import PortfolioBacktestRequest

START, END = '2022-01-03', '2023-12-29'


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


