"""[P2-13] DCA 표시용 계산(DcaCalculator)과 실제 시뮬레이션(PortfolioDcaManager)의
두 모델 불일치 검증.

**버그 요약**: `portfolio_manager_service.py`는 같은 응답 안에서 두 개의 서로 다른
DCA 실행 모델을 사용했다.

- `portfolio_dca_manager.py` (실제 시뮬레이션): Nth-weekday 스케줄을 따르고,
  회당 투자금에서 수수료를 차감한 뒤 주식 수를 계산한다
  (`invest_amount = amount * (1 - commission)`).
- `dca_calculator.py` (표시 전용, 수정 전): "예정일 이후 첫 거래일"에 매수하되
  수수료를 완전히 무시했다(`shares_bought = period_amount / price`). 게다가
  `get_next_nth_weekday`를 매번 `original_nth=None`으로 호출해 "몇 번째
  요일"을 이론상 스케줄에서 매번 다시 계산했다(실제 집행일이 아니라).

두 모델은 (a) 결측일이 낀 예정일, (b) commission > 0 조합에서 눈에 띄게
갈라졌다 -- 종목별로 표시되는 매수 단가/수익률이 포트폴리오 합계와 모순됐다.

**FIX**: `DcaCalculator.calculate_dca_shares_and_return`가 `PortfolioDcaManager`
(실제 시뮬레이션이 쓰는 바로 그 클래스)에 위임하도록 다시 작성했다. 대상 종목의
RAW 인덱스를 그대로 date_range로 사용해 미니 시뮬레이션을 구동하므로(다른
종목의 날짜가 섞여 들어오지 않는 단일 종목 문맥에서는 전체 포트폴리오
시뮬레이션에서 그 종목만 뽑아낸 것과 수학적으로 동일하다), 스케줄링과 수수료
처리가 실제 시뮬레이션과 구조적으로 일치한다.

**호출자 제약**: grep 결과 `DcaCalculator.calculate_dca_shares_and_return`의
호출자는 `portfolio_manager_service.py` 단 한 곳이며(863행 부근), 그 호출은
`request.commission`을 넘기지 않는다(5개 위치 인자만 전달:
`df, period_amount, dca_periods, request.start_date, dca_frequency`). 그
파일은 이 배치의 다른 에이전트가 소유하므로 여기서 호출부를 고칠 수 없다.
따라서 새 `commission` 파라미터는 하위 호환을 위해 `0.0` 기본값을 가지며(기존
호출은 그대로 동작), 실제 운영 경로에서 수수료를 반영하려면 그 호출부가
`request.commission`을 전달하도록 바뀌어야 한다 (별도 후속 작업, 리포트에 기록).
"""
from datetime import datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.dca_calculator import DcaCalculator
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager

pytestmark = pytest.mark.unit


def _gap_and_price_step_frame():
    """monthly_1, start=2024-01-04(1월 첫 목요일)의 두 번째 예정일인
    2024-02-01(2월 첫 목요일)이 결측이고, 그 결측 이후 가격이 바뀌는 프레임.
    """
    date_range = pd.bdate_range('2024-01-01', '2024-03-01')
    index = date_range[date_range != pd.Timestamp('2024-02-01')]
    close = pd.Series(50.0, index=index)
    close.loc[close.index >= pd.Timestamp('2024-02-02')] = 55.0
    return pd.DataFrame({'Close': close.values}, index=index)


def _drive_real_simulation_dca_manager(df, period_amount, dca_periods, start_date_str, frequency, commission):
    """PortfolioDcaManager(실제 시뮬레이션이 쓰는 바로 그 클래스)를 이 종목의
    RAW 인덱스만으로 직접 구동해 '진짜 시뮬레이션이 이 종목에 대해 실행했을
    결과'를 재현한다. DcaCalculator가 내부적으로 위임하는 대상과 동일하다."""
    manager = PortfolioDcaManager()
    start = datetime.strptime(start_date_str, '%Y-%m-%d')

    dca_info = {'X': DcaStrategyInfo(
        symbol='XXX', allocation=1.0, asset_type='stock', investment_type='dca',
        monthly_amount=period_amount, dca_frequency=frequency, dca_periods=dca_periods,
    )}
    stock_amounts = {'X': period_amount}
    shares = {'X': 0.0}
    pending = {'X'}
    prev_date = None
    purchases = []  # (date, price, shares_bought, cash_invested)

    for current_date in df.index:
        if current_date.date() < start.date():
            continue
        price = df['Close'].at[current_date]
        current_prices = {'X': float(price)} if pd.notna(price) else {}
        tradeable = set(current_prices.keys())

        before = shares['X']
        if pending:
            manager.execute_initial_purchases(
                current_date=current_date, stock_amounts=stock_amounts, current_prices=current_prices,
                dca_info=dca_info, shares=shares, commission=commission, pending_keys=pending,
                tradeable_keys=tradeable,
            )
        if prev_date is not None and prev_date != current_date:
            manager.execute_periodic_purchases(
                current_date=current_date, stock_amounts=stock_amounts, current_prices=current_prices,
                dca_info=dca_info, shares=shares, commission=commission, start_date_obj=start,
                tradeable_keys=tradeable,
            )
        if shares['X'] != before:
            purchases.append((current_date.date(), float(price), shares['X'] - before))
        prev_date = current_date

    return shares['X'], purchases


class TestDcaCalculatorMatchesSimulationOnGapPlusCommission:
    """핵심 TDD 시나리오: 예정일이 거래일이 아니고(2024-02-01 결측) 수수료가
    0보다 큰(5%) 경우에도 DcaCalculator의 표시값이 실제 시뮬레이션 실행 결과와
    일치해야 한다."""

    def test_matches_directly_driven_portfolio_dca_manager(self):
        df = _gap_and_price_step_frame()
        commission = 0.05
        period_amount = 1000.0
        dca_periods = 2  # 초회 + 2월분 1회

        real_total_shares, real_purchases = _drive_real_simulation_dca_manager(
            df, period_amount, dca_periods, '2024-01-04', 'monthly_1', commission,
        )

        total_shares, average_price, return_rate, trade_log = DcaCalculator.calculate_dca_shares_and_return(
            df, period_amount, dca_periods, '2024-01-04', 'monthly_1', commission=commission,
        )

        assert len(trade_log) == len(real_purchases) == 2, (
            f"매수 횟수가 실제 시뮬레이션과 일치해야 함: DcaCalculator={len(trade_log)}, "
            f"실제 시뮬레이션={len(real_purchases)}"
        )
        assert total_shares == pytest.approx(real_total_shares), (
            f"총 매수 주식 수가 실제 시뮬레이션과 일치해야 함: "
            f"DcaCalculator={total_shares}, 실제 시뮬레이션={real_total_shares}"
        )

        for (real_date, real_price, real_shares_bought), trade in zip(real_purchases, trade_log):
            assert trade['EntryPrice'] == pytest.approx(real_price), (
                f"{real_date}: 매수 가격 불일치 (DcaCalculator={trade['EntryPrice']}, "
                f"실제 시뮬레이션={real_price})"
            )
            assert trade['Size'] == pytest.approx(real_shares_bought), (
                f"{real_date}: 매수 주식 수 불일치 (DcaCalculator={trade['Size']}, "
                f"실제 시뮬레이션={real_shares_bought})"
            )
            assert trade['EntryTime'].startswith(real_date.isoformat()), (
                f"매수일 불일치: DcaCalculator={trade['EntryTime']}, 실제 시뮬레이션={real_date}"
            )

    def test_concrete_expected_values_gap_deferred_and_commission_applied(self):
        """수기로 계산한 구체적 기대값 (사람이 감사하기 쉬운 형태로 고정)."""
        df = _gap_and_price_step_frame()
        commission = 0.05
        period_amount = 1000.0

        total_shares, average_price, return_rate, trade_log = DcaCalculator.calculate_dca_shares_and_return(
            df, period_amount, dca_periods=2, start_date='2024-01-04',
            frequency='monthly_1', commission=commission,
        )

        expected_shares_1 = (period_amount * (1 - commission)) / 50.0   # 2024-01-04, 결측 없음
        expected_shares_2 = (period_amount * (1 - commission)) / 55.0   # 2024-02-01 결측 -> 다음 거래일(02-02)의 진짜 가격
        expected_total_shares = expected_shares_1 + expected_shares_2
        expected_total_invested = period_amount * 2  # 총 커밋 금액(수수료 차감 전)
        expected_average_price = expected_total_invested / expected_total_shares
        expected_return = (55.0 / expected_average_price - 1) * 100  # end_price = 마지막 종가(55.0)

        assert len(trade_log) == 2
        assert trade_log[0]['EntryPrice'] == 50.0
        assert trade_log[0]['EntryTime'].startswith('2024-01-04')
        assert trade_log[1]['EntryPrice'] == 55.0, (
            f"2024-02-01 결측일의 ffill/근접 가격(50.0)이 아니라 실제 집행일(02-02)의 "
            f"진짜 가격(55.0)을 써야 함. 실제 값: {trade_log[1]['EntryPrice']}"
        )
        assert trade_log[1]['EntryTime'].startswith('2024-02-02'), (
            f"예정일(02-01)이 아니라 다음 거래일(02-02)로 이연되어야 함: {trade_log[1]['EntryTime']}"
        )

        assert total_shares == pytest.approx(expected_total_shares)
        assert average_price == pytest.approx(expected_average_price)
        assert return_rate == pytest.approx(expected_return)

        # 수수료가 실제로 반영됐는지: 무시했다면(수정 전 버그) 각 회차가
        # period_amount/price 그대로였을 것이다 -- 여기서는 더 적어야 한다.
        naive_shares_ignoring_commission = period_amount / 50.0 + period_amount / 55.0
        assert total_shares < naive_shares_ignoring_commission, (
            "수수료가 반영되지 않은 것으로 보임 (수정 전 버그 재현)"
        )


class TestDcaCalculatorBackwardCompatibility:
    """기존 유일한 호출자(portfolio_manager_service.py)는 commission 인자 없이
    5개의 위치 인자만 넘긴다 -- 이 호출 방식이 계속 동작해야 한다."""

    def test_call_without_commission_argument_still_works_with_default_zero(self):
        df = _gap_and_price_step_frame()

        # portfolio_manager_service.py의 실제 호출 형태 그대로 (commission 없음)
        total_shares, average_price, return_rate, trade_log = DcaCalculator.calculate_dca_shares_and_return(
            df, 1000.0, 2, '2024-01-04', 'monthly_1',
        )

        assert len(trade_log) == 2
        assert total_shares > 0
        # commission 기본값 0.0이므로 수수료 없이 전액이 주식으로 전환되어야 함
        assert trade_log[0]['Size'] == pytest.approx(1000.0 / 50.0)
        assert trade_log[1]['Size'] == pytest.approx(1000.0 / 55.0)

    def test_lump_sum_style_single_period_regression_guard(self):
        """dca_periods=1(사실상 일시불과 유사한 극단 케이스)도 크래시 없이 동작해야 한다."""
        index = pd.bdate_range('2024-01-01', '2024-01-10')
        df = pd.DataFrame({'Close': [100.0] * len(index)}, index=index)

        total_shares, average_price, return_rate, trade_log = DcaCalculator.calculate_dca_shares_and_return(
            df, 1000.0, 1, '2024-01-01', 'monthly_1', commission=0.0,
        )

        assert len(trade_log) == 1
        assert total_shares == pytest.approx(10.0)
        assert average_price == pytest.approx(100.0)
        assert return_rate == pytest.approx(0.0, abs=1e-9)

    def test_no_price_data_returns_zero_tuple(self):
        """빈 데이터프레임이면 예전처럼 (0, 0, 0, [])을 반환해야 한다."""
        df = pd.DataFrame({'Close': []}, index=pd.DatetimeIndex([]))

        result = DcaCalculator.calculate_dca_shares_and_return(
            df, 1000.0, 3, '2024-01-01', 'monthly_1',
        )

        assert result == (0, 0, 0, [])
