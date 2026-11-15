"""PortfolioMetrics.calculate_daily_metrics_and_history 직접 단위 테스트 (P1-12).

시뮬레이션 엔진의 일일 루프가 매일 호출하는 핵심 계산 함수. 포트폴리오
가치/일간 수익률/비중을 계산하며, 특히 "당일 신규 유입 현금(DCA 등)을
수익으로 착각하지 않는다"는 불변식이 이 감사가 찾아낸 여러 분모/유입 버그
(P1-03, P1-07 등)의 핵심 메커니즘이다. 이 함수 자체를 직접 겨냥한 테스트는
지금까지 없었다 (시뮬레이션 엔진을 통한 간접 실행만 있었음).
"""
import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_metrics import PortfolioMetrics

pytestmark = pytest.mark.unit


def _stock_info(symbol: str, allocation: float = 1.0) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='stock',
        investment_type='lump_sum', monthly_amount=0.0,
    )


def _cash_info(symbol: str, allocation: float = 1.0) -> DcaStrategyInfo:
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='cash',
        investment_type='lump_sum', monthly_amount=0.0,
    )


class TestCalculateDailyMetricsAndHistory:
    def test_single_stock_ten_percent_gain_normalizes_and_returns_correctly(self):
        """10주 보유, 가격이 $10 -> $11로 10% 상승. prev_portfolio_value=100
        (어제 종가 기준 평가액)이므로 daily_return은 정확히 10%여야 한다."""
        normalized_value, daily_return, weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares={'A': 10.0},
            available_cash=0.0,
            current_prices={'A': 11.0},
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=0.0,
            total_amount=100.0,
            dca_info={'A': _stock_info('AAA')},
        )

        assert normalized_value == pytest.approx(1.10)
        assert daily_return == pytest.approx(0.10)
        assert weights['AAA'] == pytest.approx(1.0)
        assert weights['date'] == '2024-01-02'

    def test_cash_only_portfolio_is_flat_with_zero_return(self):
        shares_empty: dict = {}
        normalized_value, daily_return, weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares=shares_empty,
            available_cash=1000.0,
            current_prices={},
            cash_holdings={'CASH': 1000.0},
            prev_portfolio_value=1000.0,
            daily_cash_inflow=0.0,
            total_amount=1000.0,
            dca_info={'CASH': _cash_info('CASH')},
        )

        assert normalized_value == pytest.approx(1.0)
        assert daily_return == pytest.approx(0.0)
        assert weights['CASH'] == pytest.approx(1.0)

    def test_first_day_prev_value_zero_forces_zero_return_regardless_of_gain(self):
        """prev_portfolio_value=0.0은 '첫날'을 나타내는 센티널 값이다. 이
        날에는 실제 평가액이 얼마든 daily_return이 무조건 0.0이어야 한다
        (그렇지 않으면 첫 매수 자체가 '수익'으로 계상되는 왜곡이 생긴다)."""
        _normalized, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-01'),
            shares={'A': 50.0},
            available_cash=0.0,
            current_prices={'A': 100.0},
            cash_holdings={},
            prev_portfolio_value=0.0,
            daily_cash_inflow=5000.0,
            total_amount=5000.0,
            dca_info={'A': _stock_info('AAA')},
        )

        assert daily_return == 0.0

    def test_stock_with_no_current_price_excluded_from_value_and_weights(self):
        """B는 보유 중(shares=5)이지만 오늘 가격 정보가 없다. 이 함수 자체는
        '마지막 유효가 유지' 같은 폴백을 하지 않는다 -- current_prices에 없는
        종목은 그날의 평가액과 비중 계산 모두에서 조용히 제외된다 (그 폴백은
        시뮬레이션 엔진의 detect_and_update_delisting이 이 함수를 호출하기
        *전에* 책임진다)."""
        normalized_value, _daily_return, weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares={'A': 10.0, 'B': 5.0},
            available_cash=0.0,
            current_prices={'A': 10.0},  # B 가격 없음
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=0.0,
            total_amount=100.0,
            dca_info={'A': _stock_info('AAA'), 'B': _stock_info('BBB')},
        )

        assert normalized_value == pytest.approx(1.0)  # A의 100만 반영, B는 제외
        assert 'BBB' not in weights
        assert weights['AAA'] == pytest.approx(1.0)

    def test_mixed_stock_and_cash_weights_sum_to_one(self):
        _normalized, _daily, weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares={'A': 5.0, 'B': 2.0},
            available_cash=50.0,
            current_prices={'A': 20.0, 'B': 50.0},  # A=100, B=100
            cash_holdings={'CASH': 50.0},
            prev_portfolio_value=0.0,
            daily_cash_inflow=0.0,
            total_amount=250.0,
            dca_info={'A': _stock_info('AAA'), 'B': _stock_info('BBB'), 'CASH': _cash_info('CASH')},
        )

        assert weights['AAA'] == pytest.approx(0.4)
        assert weights['BBB'] == pytest.approx(0.4)
        assert weights['CASH'] == pytest.approx(0.2)
        total_weight = sum(v for k, v in weights.items() if k != 'date')
        assert total_weight == pytest.approx(1.0)

    def test_price_drop_yields_negative_return(self):
        _normalized_value, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares={'A': 10.0},
            available_cash=0.0,
            current_prices={'A': 9.0},
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=0.0,
            total_amount=100.0,
            dca_info={'A': _stock_info('AAA')},
        )

        assert daily_return == pytest.approx(-0.10)

    def test_same_day_cash_inflow_is_not_counted_as_investment_gain(self):
        """이 감사가 찾아낸 버그 계열(분모/유입 오류, 예: P1-07 DCA 계획-실행
        불일치)의 핵심 방어선을 직접 겨냥한 테스트다. 어제 평가액 100에서
        오늘 110으로 늘었지만, 그 중 10은 '오늘 새로 들어온 투자금'
        (daily_cash_inflow)이지 시세 상승분이 아니다. 만약 daily_cash_inflow가
        net_change 계산에서 빠지면(버그) daily_return은 잘못 +10%로 계산될
        것이다 -- 올바른 계산은 정확히 0%다."""
        _normalized, daily_return, _weights = PortfolioMetrics.calculate_daily_metrics_and_history(
            current_date=pd.Timestamp('2024-01-02'),
            shares={'A': 11.0},
            available_cash=0.0,
            current_prices={'A': 10.0},  # 11주 * $10 = $110
            cash_holdings={},
            prev_portfolio_value=100.0,
            daily_cash_inflow=10.0,  # 오늘 신규 DCA 유입액
            total_amount=110.0,
            dca_info={'A': _stock_info('AAA')},
        )

        assert daily_return == pytest.approx(0.0)
