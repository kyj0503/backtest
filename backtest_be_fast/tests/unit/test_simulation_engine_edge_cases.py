"""PortfolioSimulationEngine 일일 루프의 경계 조건 테스트 (P1-12).

기존 테스트(test_simulation_engine_fx_failure.py, test_simulation_engine_async_offload.py,
test_dca_schedule_alignment.py)는 각각 환율 실패, 이벤트 루프 비블로킹,
DCA 스케줄 정합성이라는 좁은 버그를 겨냥한다. 이 파일은 그보다 더 기본적인
"엔진에 극단적인 입력을 주면 일일 루프가 어떻게 동작하는가"를 다룬다:
가격 데이터 완전 결측, 하루짜리 백테스트, 현금 전용 포트폴리오, 단일 자산
100% 배분, 윤년 2/29, 가격 데이터 중간의 NaN.

일부 테스트는 '올바른 동작'이 아니라 '현재 동작을 있는 그대로 문서화'하는
목적이다 (프로덕션 코드 수정은 이 작업 범위 밖이므로) -- 각 테스트의 주석에
명시했다.
"""
import asyncio
from datetime import datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine

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


def _flat_price_frame(start, end, price: float = 100.0) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _run(engine: PortfolioSimulationEngine, **kwargs) -> pd.DataFrame:
    return asyncio.run(engine.execute_simulation(**kwargs))


class TestMissingOrEmptyPriceData:
    """종목에 가격 데이터가 전혀 없을 때(심볼이 portfolio_data에서 아예 빠지거나,
    존재해도 0행인 경우) 그 종목에 배정된 자본이 어떻게 되는지 문서화한다.

    **현재 동작(수정하지 않고 있는 그대로 고정)**: 그 자본은 available_cash에도
    보유 주식 평가액에도 반영되지 않는다 -- 에러나 경고 없이 포트폴리오
    평가액 계산에서 조용히 빠진다. pending_initial_keys가 매일 재시도하지만
    가격이 끝내 나타나지 않으므로 영원히 미매수 상태로 남는다.
    """

    def test_symbol_entirely_absent_from_portfolio_data_never_gets_invested(self):
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 5)
        date_range = pd.bdate_range(start=start, end=end)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={'A': 600.0, 'B': 400.0},
            amounts={'A': 600.0, 'B': 400.0},
            cash_amount=0.0, total_amount=1000.0,
            portfolio_data={'AAA': _flat_price_frame(start, end)},  # BBB 키 자체가 없음
            dca_info={'A': _stock_info('AAA'), 'B': _stock_info('BBB')},
            ticker_currencies={'A': 'USD', 'B': 'USD'},
            exchange_rates_by_currency={}, rebalance_frequency='none', commission=0.0,
        )

        # A의 $600만 투자되고(가격 $100 -> 6주), B의 $400은 어디에도 반영되지
        # 않아 포트폴리오 가치가 총투자금 대비 0.6배로 고정된다.
        assert result['Portfolio_Value'].tolist() == pytest.approx([0.6] * len(result))
        assert result.attrs['total_trades'] == 1  # A만 매수됨

    def test_empty_dataframe_for_symbol_behaves_same_as_missing_symbol(self):
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 5)
        date_range = pd.bdate_range(start=start, end=end)
        empty_df = pd.DataFrame({'Close': []})
        empty_df.index = pd.to_datetime(empty_df.index)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={'A': 600.0, 'B': 400.0},
            amounts={'A': 600.0, 'B': 400.0},
            cash_amount=0.0, total_amount=1000.0,
            portfolio_data={'AAA': _flat_price_frame(start, end), 'BBB': empty_df},
            dca_info={'A': _stock_info('AAA'), 'B': _stock_info('BBB')},
            ticker_currencies={'A': 'USD', 'B': 'USD'},
            exchange_rates_by_currency={}, rebalance_frequency='none', commission=0.0,
        )

        assert result['Portfolio_Value'].tolist() == pytest.approx([0.6] * len(result))
        assert result.attrs['total_trades'] == 1


class TestSingleDayBacktest:
    def test_single_day_full_investment_normalizes_to_one(self):
        engine = PortfolioSimulationEngine()
        start = end = datetime(2024, 1, 2)  # 화요일 (영업일)
        date_range = pd.bdate_range(start=start, end=end)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={'A': 1000.0}, amounts={'A': 1000.0},
            cash_amount=0.0, total_amount=1000.0,
            portfolio_data={'AAA': _flat_price_frame(start, end)},
            dca_info={'A': _stock_info('AAA')}, ticker_currencies={'A': 'USD'},
            exchange_rates_by_currency={}, rebalance_frequency='none', commission=0.0,
        )

        assert len(result) == 1
        assert result['Portfolio_Value'].iloc[0] == pytest.approx(1.0)
        assert result['Daily_Return'].iloc[0] == pytest.approx(0.0)
        assert result['Cumulative_Return'].iloc[0] == pytest.approx(0.0)
        assert result.attrs['total_trades'] == 1


class TestCashOnlyPortfolio:
    def test_pure_cash_portfolio_stays_flat_and_never_rebalances(self):
        """자산이 현금 하나뿐이면 target_weights도 원소가 1개뿐이라, 리밸런싱
        주기가 설정돼 있어도 `len(target_weights) > 1` 가드에 걸려 리밸런싱
        로직 자체가 절대 실행되지 않는다."""
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 15)
        date_range = pd.bdate_range(start=start, end=end)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={}, amounts={'CASH': 1000.0},
            cash_amount=1000.0, total_amount=1000.0,
            portfolio_data={},
            dca_info={'CASH': _cash_info('CASH')}, ticker_currencies={},
            exchange_rates_by_currency={}, rebalance_frequency='monthly_1', commission=0.0,
        )

        assert result['Portfolio_Value'].tolist() == pytest.approx([1.0] * len(result))
        assert result['Daily_Return'].tolist() == pytest.approx([0.0] * len(result))
        assert result.attrs['total_trades'] == 0
        assert result.attrs['rebalance_history'] == []


class TestSingleAssetFullAllocation:
    def test_hundred_percent_allocation_growth_matches_hand_calc(self):
        """단일 자산 100% 배분, 수수료 0. 3영업일 가격 [100, 120, 90]에 대해
        정규화 가치/일간 수익률을 손으로 계산해 대조한다."""
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)  # 월요일
        end = datetime(2024, 1, 3)    # 수요일
        date_range = pd.bdate_range(start=start, end=end)  # 월,화,수 = 3영업일
        df = pd.DataFrame({'Close': [100.0, 120.0, 90.0]}, index=date_range)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={'A': 1000.0}, amounts={'A': 1000.0},
            cash_amount=0.0, total_amount=1000.0,
            portfolio_data={'AAA': df},
            dca_info={'A': _stock_info('AAA')}, ticker_currencies={'A': 'USD'},
            exchange_rates_by_currency={}, rebalance_frequency='none', commission=0.0,
        )

        assert result['Portfolio_Value'].tolist() == pytest.approx([1.0, 1.2, 0.9])
        # Day1: 첫날이라 prev=0 센티널 -> 0.0. Day2: (1200-1000)/1000=0.20. Day3: (900-1200)/1200=-0.25.
        assert result['Daily_Return'].tolist() == pytest.approx([0.0, 0.20, -0.25])
        assert result['Cumulative_Return'].tolist() == pytest.approx([0.0, 20.0, -10.0])


class TestLeapDaySpan:
    def test_feb_29_included_and_priced_correctly(self):
        """2024-02-29(윤년의 2월 29일, 목요일=영업일)가 날짜 범위에서 누락되거나
        중복 계산되지 않는지, 그리고 그날의 가격이 정확히 반영되는지 확인한다."""
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 2, 27)  # 화요일
        end = datetime(2024, 3, 1)     # 금요일
        date_range = pd.bdate_range(start=start, end=end)  # 화27,수28,목29,금1 = 4영업일
        df = pd.DataFrame({'Close': [100.0, 101.0, 102.0, 103.0]}, index=date_range)

        result = _run(
            engine,
            date_range=date_range, start_date_obj=start, end_date_obj=end,
            stock_amounts={'A': 1000.0}, amounts={'A': 1000.0},
            cash_amount=0.0, total_amount=1000.0,
            portfolio_data={'AAA': df},
            dca_info={'A': _stock_info('AAA')}, ticker_currencies={'A': 'USD'},
            exchange_rates_by_currency={}, rebalance_frequency='none', commission=0.0,
        )

        assert len(result) == 4
        leap_day = pd.Timestamp('2024-02-29')
        assert leap_day in result.index
        assert result.loc[leap_day, 'Portfolio_Value'] == pytest.approx(1.02)  # 102/100


class TestNaNInPriceFrame:
    def test_mid_series_nan_close_is_forward_filled_not_propagated(self):
        """가격 프레임 중간에 단일 NaN(예: 데이터 제공사의 결측치)이 있으면,
        _pre_calculate_prices의 reindex+ffill 단계에서 직전 유효 종가로 조용히
        채워진다 -- NaN이 그대로 전파되거나 예외가 발생하지 않는다. 이 동작은
        휴장일 처리와 동일한 메커니즘(ffill)을 공유하므로, '진짜 결측(휴장일)'과
        '데이터 오류(NaN)'를 이 계층에서는 구분하지 않는다는 뜻이기도 하다."""
        engine = PortfolioSimulationEngine()
        date_range = pd.bdate_range(start='2024-01-01', end='2024-01-04')  # 월~목, 4영업일
        df = pd.DataFrame({'Close': [100.0, float('nan'), 102.0, 103.0]}, index=date_range)

        aligned_prices, _rates = engine._pre_calculate_prices(
            date_range=date_range, stock_amounts={'A': 1000.0},
            portfolio_data={'AAA': df}, dca_info={'A': _stock_info('AAA')},
            ticker_currencies={'A': 'USD'}, exchange_rates_by_currency={},
        )

        assert aligned_prices['A'].tolist() == pytest.approx([100.0, 100.0, 102.0, 103.0])
