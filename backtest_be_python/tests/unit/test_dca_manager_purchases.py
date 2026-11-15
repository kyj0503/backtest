"""PortfolioDcaManager 직접 단위 테스트 (P1-12).

기존 테스트(test_dca_schedule_alignment.py)는 PortfolioManagerService를 통한
전체 파이프라인에서 "계획 vs 실행 정합성"(총수익률 불변식)을 검증하지만,
PortfolioDcaManager의 개별 메서드(execute_initial_purchases /
execute_periodic_purchases)를 직접 호출해서 매수 주식 수/현금 유입액을
손으로 계산한 값과 정확히 대조하는 테스트는 없었다. 이 파일은 그 간극을
메운다: 수수료 경계값(0과 스키마 상한 부근), 0/음수 가격, DCA 초회 매수가
어떤 필드를 사용하는지, 그리고 DCA 총 횟수 소진 후 매수가 멈추는지를
직접 검증한다.
"""
from datetime import date, datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager

pytestmark = pytest.mark.unit


def _lump_sum_info(symbol: str) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=1.0, asset_type='stock',
        investment_type='lump_sum', monthly_amount=0.0,
    )


def _dca_info(symbol: str, monthly_amount: float, dca_periods: int,
              dca_frequency: str = 'weekly_1', **overrides) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=1.0, asset_type='stock',
        investment_type='dca', monthly_amount=monthly_amount,
        dca_frequency=dca_frequency, dca_periods=dca_periods, **overrides,
    )


class TestInitialPurchaseCommissionBoundaries:
    """스키마의 commission 필드는 `Field(0.002, ge=0, lt=0.1)` -- 0은 포함,
    0.1은 배타적 상한이다. 두 경계 근처에서 수수료 차감이 정확한지 확인한다."""

    def test_zero_commission_boundary(self):
        manager = PortfolioDcaManager()
        shares: dict = {}
        trades, cash_inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-01'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 100.0},
            dca_info={'A': _lump_sum_info('AAA')},
            shares=shares, commission=0.0,
        )

        assert trades == 1
        assert cash_inflow == pytest.approx(1000.0)
        assert shares['A'] == pytest.approx(10.0)

    def test_commission_just_under_schema_max_boundary(self):
        manager = PortfolioDcaManager()
        shares: dict = {}
        commission = 0.0999999  # lt=0.1 경계에 최대한 가까운 값
        trades, cash_inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-01'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 100.0},
            dca_info={'A': _lump_sum_info('AAA')},
            shares=shares, commission=commission,
        )

        expected_invest_amount = 1000.0 * (1 - commission)
        assert trades == 1
        assert cash_inflow == pytest.approx(1000.0)  # 유입액 자체는 수수료 차감 전 명목 투자액
        assert shares['A'] == pytest.approx(expected_invest_amount / 100.0)


class TestZeroAndNegativePrices:
    def test_zero_price_is_skipped_instead_of_crashing(self):
        """데이터 결측/오류로 가격 0이 유입되면 ZeroDivisionError로 요청 전체를
        깨뜨리는 대신 그 종목의 체결만 건너뛴다 (P1-18)."""
        manager = PortfolioDcaManager()
        shares: dict = {}
        trades, inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-01'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 0.0},
            dca_info={'A': _lump_sum_info('AAA')},
            shares=shares, commission=0.0,
        )

        assert trades == 0
        assert inflow == 0.0
        assert 'A' not in shares

    def test_negative_price_is_skipped_instead_of_creating_negative_shares(self):
        """음수 가격은 음수 보유 수량을 만드는 대신 체결을 건너뛴다 (P1-18)."""
        manager = PortfolioDcaManager()
        shares: dict = {}
        trades, inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-01'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': -10.0},
            dca_info={'A': _lump_sum_info('AAA')},
            shares=shares, commission=0.0,
        )

        assert trades == 0
        assert inflow == 0.0
        assert 'A' not in shares


class TestDcaFirstPurchaseUsesMonthlyAmountNotStockAmount:
    def test_dca_initial_purchase_ignores_stock_amounts_value(self):
        """DCA 종목의 초회 매수는 stock_amounts[key](총 계획 투자액)가 아니라
        dca_info.monthly_amount(회당 금액)만 사용한다. stock_amounts에 훨씬
        큰 값(총 계획액)을 넣어도 초회 매수 금액에는 영향이 없어야 한다."""
        manager = PortfolioDcaManager()
        info = _dca_info('AAA', monthly_amount=200.0, dca_periods=12)
        shares: dict = {}
        trades, cash_inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-01'),
            stock_amounts={'A': 2400.0},  # 총 계획액(12회 * 200) -- 초회엔 쓰이지 않음
            current_prices={'A': 50.0},
            dca_info={'A': info},
            shares=shares, commission=0.0,
        )

        assert trades == 1
        assert cash_inflow == pytest.approx(200.0)
        assert shares['A'] == pytest.approx(4.0)
        assert info.executed_count == 1


class TestPeriodicPurchaseStopsWhenPeriodsExhausted:
    """동일한 '매수 예정일 도래' 조건에서, executed_count가 dca_periods에
    도달했는지 여부만 다르게 해서 대조한다 (한쪽은 매수, 한쪽은 스킵)."""

    def _due_date_info(self, executed_count: int, dca_periods: int = 2) -> DcaStrategyInfo:
        return _dca_info(
            'AAA', monthly_amount=200.0, dca_periods=dca_periods,
            dca_frequency='weekly_1',
            executed_count=executed_count,
            last_dca_date=date(2024, 1, 1),
            original_nth_weekday=1,
        )

    def test_purchase_executes_when_periods_remain(self):
        manager = PortfolioDcaManager()
        info = self._due_date_info(executed_count=1)
        shares = {'A': 8.0}

        trades, cash_inflow = manager.execute_periodic_purchases(
            current_date=pd.Timestamp('2024-01-08'),  # last_dca_date(1/1) + 1주 = 예정일
            stock_amounts={'A': 999.0},
            current_prices={'A': 50.0},
            dca_info={'A': info},
            shares=shares, commission=0.0,
            start_date_obj=datetime(2024, 1, 1),
        )

        assert trades == 1
        assert cash_inflow == pytest.approx(200.0)
        assert shares['A'] == pytest.approx(12.0)  # 8 + 200/50
        assert info.executed_count == 2
        assert info.last_dca_date == date(2024, 1, 8)

    def test_no_purchase_once_dca_periods_exhausted(self):
        """동일한 '매수 예정일 도래' 조건이지만 executed_count가 이미
        dca_periods에 도달했으므로 매수가 발생하면 안 된다."""
        manager = PortfolioDcaManager()
        info = self._due_date_info(executed_count=2, dca_periods=2)
        shares = {'A': 8.0}

        trades, cash_inflow = manager.execute_periodic_purchases(
            current_date=pd.Timestamp('2024-01-08'),
            stock_amounts={'A': 999.0},
            current_prices={'A': 50.0},
            dca_info={'A': info},
            shares=shares, commission=0.0,
            start_date_obj=datetime(2024, 1, 1),
        )

        assert trades == 0
        assert cash_inflow == pytest.approx(0.0)
        assert shares['A'] == pytest.approx(8.0)  # 변화 없음
        assert info.executed_count == 2  # 변화 없음
