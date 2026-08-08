"""[P2-14] 밸류에이션 가격과 거래 가능 가격의 혼동 분리 검증.

**버그 요약**: `_pre_calculate_prices`가 만드는 `aligned_prices`는 각 종목의
Close를 date_range(모든 종목 날짜의 합집합) 기준으로 reindex한 뒤 ffill한
시리즈다. 이 값은 (a) 일별 포트폴리오 평가, (b) 거래 실행 여부 판단(초기 매수,
DCA 정기 매수, 리밸런싱), (c) 상장폐지 감지 세 곳에 그대로 재사용됐다.

- (a)는 정당하다 -- 휴장일에도 마지막 가격으로 마킹하는 것은 올바른 평가 방식.
- (b)는 버그다 -- 한쪽 시장이 쉬는 날, 그 종목의 ffill된(어제자) 가격을 "오늘의
  거래 가능 가격"으로 착각해 존재하지 않았던 가격에 거래를 체결시킨다.
- (c)는 버그다 -- ffill은 무한정 이전 값을 반복하므로, 종목이 사라진 뒤에도
  `current_prices`에는 영원히 값이 남아 있어 `last_price_date` 갱신이 멈추지
  않고, 상장폐지가 영영 감지되지 않는다.

FIX: `_pre_calculate_prices`(밸류에이션용, 변경 없음)와 별도로, RAW 프레임에서
직접 파생한 "당일 실제로 관측되었는가" 불리언 마스크를 추가한다
(`_pre_calculate_tradeable_mask` / `_get_daily_tradeable_keys`). 거래 실행
함수들과 `detect_and_update_delisting`은 이 마스크를 근거로 삼고, 평가
로직(`calculate_daily_metrics_and_history`)은 계속 ffill된 `current_prices`를
사용한다.

이 파일은 A/B 두 종목이 서로 다른 날짜에 결측치를 갖는 "혼합 시장" 픽스처로
세 가지를 검증한다:
1. 관측되지 않은 날짜에는 어떤 거래(초기 매수/DCA 정기 매수/리밸런싱)도
   실행되지 않는다.
2. 평가(valuation)는 관측되지 않은 날짜에도 마지막 관측 가격으로 계속된다.
3. 원본 데이터가 중간에 끊긴 종목은 (ffill로 가려지지 않고) 올바른 시점에
   상장폐지로 감지된다.
"""
import asyncio
from datetime import date, datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine

pytestmark = pytest.mark.unit


def _stock_info(symbol, allocation, investment_type='lump_sum', monthly_amount=0.0,
                 dca_frequency='monthly_1', dca_periods=0):
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='stock',
        investment_type=investment_type, monthly_amount=monthly_amount,
        dca_frequency=dca_frequency, dca_periods=dca_periods,
    )


def _cash_info(symbol, allocation):
    return DcaStrategyInfo(
        symbol=symbol, allocation=allocation, asset_type='cash',
        investment_type='lump_sum', monthly_amount=0.0,
    )


class TestTradeableMaskDerivedFromRawObservation:
    """_pre_calculate_tradeable_mask가 RAW 인덱스만을 근거로 마스크를 만드는지 검증."""

    def _mixed_market_setup(self):
        engine = PortfolioSimulationEngine()
        date_range = pd.date_range('2024-01-01', '2024-01-05', freq='D')
        a_index = date_range.delete(2)  # A: 2024-01-03 결측 (예: A만의 휴장일)
        b_index = date_range.delete(1)  # B: 2024-01-02 결측 (예: B만의 휴장일)

        portfolio_data = {
            'AAA': pd.DataFrame({'Close': [100.0] * len(a_index)}, index=a_index),
            'BBB': pd.DataFrame({'Close': [50.0] * len(b_index)}, index=b_index),
        }
        dca_info = {'A': _stock_info('AAA', 0.5), 'B': _stock_info('BBB', 0.5)}
        stock_amounts = {'A': 500.0, 'B': 500.0}
        return engine, date_range, stock_amounts, portfolio_data, dca_info

    def test_mask_is_false_exactly_on_the_symbols_own_missing_dates(self):
        engine, date_range, stock_amounts, portfolio_data, dca_info = self._mixed_market_setup()

        mask = engine._pre_calculate_tradeable_mask(
            date_range=date_range, stock_amounts=stock_amounts,
            portfolio_data=portfolio_data, dca_info=dca_info,
        )

        assert mask['A'].at[pd.Timestamp('2024-01-03')] == False
        assert mask['B'].at[pd.Timestamp('2024-01-02')] == False

        # 자기 자신의 데이터가 있는 날짜는 전부 True여야 한다 (다른 종목의
        # 결측일과 섞여서는 안 된다).
        a_true_dates = mask['A'].drop(pd.Timestamp('2024-01-03'))
        b_true_dates = mask['B'].drop(pd.Timestamp('2024-01-02'))
        assert a_true_dates.all(), a_true_dates
        assert b_true_dates.all(), b_true_dates

        # 교차 오염 없음: A의 결측일에도 B는 True(자기 데이터가 있으므로), 반대도 마찬가지.
        assert mask['B'].at[pd.Timestamp('2024-01-03')] == True
        assert mask['A'].at[pd.Timestamp('2024-01-02')] == True

    def test_daily_lookup_returns_only_keys_actually_observed_that_day(self):
        engine, date_range, stock_amounts, portfolio_data, dca_info = self._mixed_market_setup()
        aligned_tradeable = engine._pre_calculate_tradeable_mask(
            date_range=date_range, stock_amounts=stock_amounts,
            portfolio_data=portfolio_data, dca_info=dca_info,
        )

        jan2 = engine._get_daily_tradeable_keys(pd.Timestamp('2024-01-02'), aligned_tradeable)
        jan3 = engine._get_daily_tradeable_keys(pd.Timestamp('2024-01-03'), aligned_tradeable)
        jan4 = engine._get_daily_tradeable_keys(pd.Timestamp('2024-01-04'), aligned_tradeable)

        assert jan2 == {'A'}, "2024-01-02: B가 결측이므로 A만 거래 가능해야 함"
        assert jan3 == {'B'}, "2024-01-03: A가 결측이므로 B만 거래 가능해야 함"
        assert jan4 == {'A', 'B'}, "둘 다 데이터가 있는 날은 둘 다 거래 가능해야 함"

    def test_symbol_entirely_absent_from_portfolio_data_is_never_tradeable(self):
        """portfolio_data에 아예 없는 종목(_pre_calculate_prices도 skip하는 경우)은
        어느 날짜에도 거래 가능 키로 나오면 안 된다."""
        engine = PortfolioSimulationEngine()
        date_range = pd.date_range('2024-01-01', '2024-01-03', freq='D')
        dca_info = {'A': _stock_info('AAA', 1.0)}
        stock_amounts = {'A': 1000.0}

        aligned_tradeable = engine._pre_calculate_tradeable_mask(
            date_range=date_range, stock_amounts=stock_amounts,
            portfolio_data={},  # AAA 데이터 자체가 없음
            dca_info=dca_info,
        )
        for d in date_range:
            assert engine._get_daily_tradeable_keys(d, aligned_tradeable) == set()


class TestDelistingDecidedFromRawObservationNotFfill:
    """detect_and_update_delisting이 ffill된 current_prices가 아니라
    tradeable_today(RAW 관측)를 근거로 상장폐지를 판단하는지 검증."""

    def test_symbol_flagged_delisted_30_days_after_last_raw_observation_despite_ever_present_ffilled_price(self):
        """[핵심/RED 재현] current_prices는 aligned_prices의 ffill 특성 그대로
        '영원히' 값을 갖고 있다고 가정한다(운영 코드의 실제 동작과 동일). 이
        상태만으로는 상장폐지가 감지되면 안 되고, tradeable_today가 30일 이상
        False일 때만 감지되어야 한다.

        수정 전 실측(스크립트로 확인): 61일 시뮬레이션에서 B가 5일째 이후
        56일간 원본 데이터가 없어도 delisted_stocks는 끝까지 set()이었다
        (current_prices는 매일 $50.0을 보고했으므로).
        """
        engine = PortfolioSimulationEngine()
        stock_amounts = {'B': 500.0}
        dca_info = {'B': _stock_info('BBB', 1.0)}

        delisted_stocks = set()
        last_valid_prices = {}
        last_price_date = {}

        start = pd.Timestamp('2024-01-01')
        for offset in range(0, 40):
            current_date = start + pd.Timedelta(days=offset)
            # current_prices는 실제 aligned_prices(ffill)처럼 절대 비지 않는다.
            current_prices = {'B': 50.0}
            tradeable_today = {'B'} if offset == 0 else set()

            engine.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices=current_prices,
                tradeable_today=tradeable_today,
                dca_info=dca_info,
                delisted_stocks=delisted_stocks,
                last_valid_prices=last_valid_prices,
                last_price_date=last_price_date,
            )

            if offset == 29:
                assert 'B' not in delisted_stocks, (
                    f"day {offset}: 아직 30일이 안 됐으므로 상장폐지로 판단하면 안 됨"
                )
            if offset == 30:
                assert 'B' in delisted_stocks, (
                    f"day {offset}: 마지막 RAW 관측 이후 30일이 지났으므로 "
                    f"상장폐지로 판단되어야 함 (current_prices는 여전히 $50.0을 보고 중이었음)"
                )

        assert 'B' in delisted_stocks

    def test_symbol_never_delisted_while_still_being_raw_observed_daily(self):
        """회귀 가드: 매일 실제로 관측되는 종목은 상장폐지로 판단되면 안 된다."""
        engine = PortfolioSimulationEngine()
        stock_amounts = {'A': 500.0}
        dca_info = {'A': _stock_info('AAA', 1.0)}

        delisted_stocks = set()
        last_valid_prices = {}
        last_price_date = {}
        start = pd.Timestamp('2024-01-01')

        for offset in range(0, 60):
            current_date = start + pd.Timedelta(days=offset)
            engine.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices={'A': 100.0},
                tradeable_today={'A'},
                dca_info=dca_info,
                delisted_stocks=delisted_stocks,
                last_valid_prices=last_valid_prices,
                last_price_date=last_price_date,
            )

        assert delisted_stocks == set()

    def test_relisting_clears_delisted_status_on_raw_reappearance(self):
        """회귀 가드: 상장폐지 이후 RAW 데이터가 다시 나타나면(재상장) 상태가 해제된다."""
        engine = PortfolioSimulationEngine()
        stock_amounts = {'B': 500.0}
        dca_info = {'B': _stock_info('BBB', 1.0)}

        delisted_stocks = set()
        last_valid_prices = {}
        last_price_date = {}
        start = pd.Timestamp('2024-01-01')

        for offset in range(0, 31):
            current_date = start + pd.Timedelta(days=offset)
            tradeable_today = {'B'} if offset == 0 else set()
            engine.detect_and_update_delisting(
                current_date=current_date, stock_amounts=stock_amounts,
                current_prices={'B': 50.0}, tradeable_today=tradeable_today,
                dca_info=dca_info, delisted_stocks=delisted_stocks,
                last_valid_prices=last_valid_prices, last_price_date=last_price_date,
            )
        assert 'B' in delisted_stocks

        reappear_date = start + pd.Timedelta(days=31)
        engine.detect_and_update_delisting(
            current_date=reappear_date, stock_amounts=stock_amounts,
            current_prices={'B': 52.0}, tradeable_today={'B'},
            dca_info=dca_info, delisted_stocks=delisted_stocks,
            last_valid_prices=last_valid_prices, last_price_date=last_price_date,
        )
        assert 'B' not in delisted_stocks


class TestPeriodicPurchaseOnlyExecutesWhenObservedToday:
    """DCA 정기 매수가 tradeable_keys를 근거로 게이팅되는지 검증 (핵심 RED 시나리오)."""

    def _mixed_market_dca_setup(self, second_price=55.0):
        """B의 DCA 스케줄(monthly_1, start=2024-01-04)의 두 번째 예정일이
        2024-02-01(B만의 결측일)에 정확히 걸리도록 구성한 픽스처.

        수정 전 실측(스크립트로 확인): 이 시나리오에서 기존 코드는
        2024-02-01에 정확히 매수를 실행했고, 그날 B의 RAW 데이터가 없었음에도
        ffill된 $50.0(전일 종가)을 매수 가격으로 사용했다.
        """
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 4)  # 목요일, 1월의 1번째 목요일
        date_range = pd.bdate_range('2024-01-01', '2024-03-01')
        b_index = date_range[date_range != pd.Timestamp('2024-02-01')]

        b_close = pd.Series(50.0, index=b_index)
        b_close.loc[b_close.index >= pd.Timestamp('2024-02-02')] = second_price

        # dca_periods=2 (초회 + 2월분 1회)로 제한한다. get_next_nth_weekday는
        # 기준일(reference_date) 자체의 요일로 다음 목표월의 요일을 다시
        # 계산하므로 (locked되는 건 "몇 번째"라는 순번뿐), 2월 매수가 결측으로
        # 다른 요일(금요일)로 이연되면 3월 목표일도 원래의 목요일이 아닌
        # 금요일 기준으로 계산된다 -- 이는 이 테스트의 관심사가 아닌
        # rebalance_helper.py의 기존 동작이므로, 3회차까지 가지 않도록
        # dca_periods를 좁혀 핵심 주장(결측일 회피 + 이연 매수가 진짜 가격을
        # 씀)에만 집중한다.
        portfolio_data = {'BBB': pd.DataFrame({'Close': b_close.values}, index=b_index)}
        dca_info = {'B': _stock_info(
            'BBB', 1.0, investment_type='dca', monthly_amount=1000.0,
            dca_frequency='monthly_1', dca_periods=2,
        )}
        stock_amounts = {'B': 1000.0}

        aligned_prices, aligned_rates = engine._pre_calculate_prices(
            date_range=date_range, stock_amounts=stock_amounts, portfolio_data=portfolio_data,
            dca_info=dca_info, ticker_currencies={'B': 'USD'}, exchange_rates_by_currency={},
        )
        aligned_tradeable = engine._pre_calculate_tradeable_mask(
            date_range=date_range, stock_amounts=stock_amounts,
            portfolio_data=portfolio_data, dca_info=dca_info,
        )
        return engine, start, date_range, stock_amounts, dca_info, aligned_prices, aligned_rates, aligned_tradeable

    def test_setup_sanity_gap_day_has_stale_ffilled_price_but_is_not_tradeable(self):
        """픽스처 자체 검증: 2024-02-01은 ffill로는 여전히 $50.0을 보고하지만,
        tradeable 마스크에서는 False여야 한다."""
        (engine, start, date_range, stock_amounts, dca_info,
         aligned_prices, aligned_rates, aligned_tradeable) = self._mixed_market_dca_setup()

        assert pd.Timestamp('2024-02-01') not in pd.DatetimeIndex(
            [d for d in date_range if aligned_tradeable['B'].at[d]]
        ) or True  # 아래 직접 단언으로 대체
        assert aligned_prices['B'].at[pd.Timestamp('2024-02-01')] == 50.0
        assert aligned_tradeable['B'].at[pd.Timestamp('2024-02-01')] == False

    def _drive_simulation(self, engine, start, date_range, stock_amounts, dca_info,
                           aligned_prices, aligned_rates, aligned_tradeable):
        dca_manager = PortfolioDcaManager()
        shares = {'B': 0.0}
        pending = {'B'}
        last_valid_exchange_rates = {}
        prev_date = None
        executed_on = []

        for current_date in date_range:
            if current_date.date() < start.date():
                continue
            current_prices, last_valid_exchange_rates = engine._get_daily_prices_from_aligned(
                current_date=current_date, aligned_prices=aligned_prices, aligned_exchange_rates=aligned_rates,
                ticker_currencies={'B': 'USD'}, last_valid_exchange_rates=last_valid_exchange_rates,
            )
            tradeable_today = engine._get_daily_tradeable_keys(current_date, aligned_tradeable)

            if pending:
                dca_manager.execute_initial_purchases(
                    current_date=current_date, stock_amounts=stock_amounts, current_prices=current_prices,
                    dca_info=dca_info, shares=shares, commission=0.0, pending_keys=pending,
                    tradeable_keys=tradeable_today,
                )
            if prev_date is not None and prev_date != current_date:
                before = shares['B']
                dca_manager.execute_periodic_purchases(
                    current_date=current_date, stock_amounts=stock_amounts,
                    current_prices=current_prices, dca_info=dca_info, shares=shares, commission=0.0,
                    start_date_obj=start, tradeable_keys=tradeable_today,
                )
                if shares['B'] != before:
                    executed_on.append((current_date.date(), current_prices.get('B'), shares['B'] - before))
            prev_date = current_date

        return executed_on

    def test_no_purchase_on_the_day_the_symbol_is_not_observed(self):
        (engine, start, date_range, stock_amounts, dca_info,
         aligned_prices, aligned_rates, aligned_tradeable) = self._mixed_market_dca_setup()

        executed_on = self._drive_simulation(
            engine, start, date_range, stock_amounts, dca_info,
            aligned_prices, aligned_rates, aligned_tradeable,
        )

        purchase_dates = [e[0] for e in executed_on]
        assert date(2024, 2, 1) not in purchase_dates, (
            "BBB가 원본 데이터를 갖지 않은 2024-02-01에 매수가 실행되면 안 됨"
        )

    def test_deferred_purchase_executes_on_next_observed_day_at_the_real_price(self):
        (engine, start, date_range, stock_amounts, dca_info,
         aligned_prices, aligned_rates, aligned_tradeable) = self._mixed_market_dca_setup(second_price=55.0)

        executed_on = self._drive_simulation(
            engine, start, date_range, stock_amounts, dca_info,
            aligned_prices, aligned_rates, aligned_tradeable,
        )

        feb_purchases = [e for e in executed_on if e[0] >= date(2024, 2, 1)]
        assert len(feb_purchases) == 1, f"2월 회차는 정확히 1번만 집행되어야 함 (유실도, 중복도 안 됨): {feb_purchases}"

        purchase_date, price_used, shares_bought = feb_purchases[0]
        assert purchase_date == date(2024, 2, 2), "다음 관측 가능일(2024-02-02)로 이연되어야 함"
        assert price_used == 55.0, (
            f"이연된 매수는 실제 집행일의 진짜 가격을 사용해야 함 "
            f"(결측일의 ffill된 $50.0이 아니라). 실제 사용된 가격: {price_used}"
        )
        assert shares_bought == pytest.approx(1000.0 / 55.0)


class TestInitialPurchaseGatedByTradeability:
    """execute_initial_purchases가 tradeable_keys를 받아 처리해도 기존 재시도
    동작(P1-08, test_dca_schedule_alignment.py)이 깨지지 않는지 확인."""

    def test_pending_key_not_bought_on_a_day_with_only_a_stale_price(self):
        """current_prices에 값이 있어도(ffill을 흉내) tradeable_keys에 없으면
        매수하면 안 되고, pending_keys에 남아 다음날 재시도되어야 한다."""
        manager = PortfolioDcaManager()
        dca_info = {'A': _stock_info('AAA', 1.0)}
        shares = {'A': 0.0}
        pending = {'A'}

        # Day 1: 가격은 있지만(ffill을 흉내) 오늘 관측되지 않았다고 가정
        trades, inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-02'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 99.0},  # stale
            dca_info=dca_info,
            shares=shares,
            commission=0.0,
            pending_keys=pending,
            tradeable_keys=set(),  # 오늘은 관측되지 않음
        )

        assert trades == 0
        assert shares['A'] == 0.0
        assert 'A' in pending, "관측되지 않은 날은 pending에 남아 다음날 재시도해야 함"

        # Day 2: 이제 관측됨
        trades, inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-03'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 100.0},
            dca_info=dca_info,
            shares=shares,
            commission=0.0,
            pending_keys=pending,
            tradeable_keys={'A'},
        )
        assert trades == 1
        assert shares['A'] == pytest.approx(10.0)
        assert 'A' not in pending

    def test_tradeable_keys_none_falls_back_to_current_prices_only(self):
        """tradeable_keys를 넘기지 않으면(None) 기존처럼 current_prices 유무만으로
        판단한다 (하위 호환)."""
        manager = PortfolioDcaManager()
        dca_info = {'A': _stock_info('AAA', 1.0)}
        shares = {'A': 0.0}
        pending = {'A'}

        trades, inflow = manager.execute_initial_purchases(
            current_date=pd.Timestamp('2024-01-02'),
            stock_amounts={'A': 1000.0},
            current_prices={'A': 100.0},
            dca_info=dca_info,
            shares=shares,
            commission=0.0,
            pending_keys=pending,
        )
        assert trades == 1
        assert shares['A'] == pytest.approx(10.0)


class TestRebalancingHoldsSymbolNotObservedToday:
    """리밸런싱이 당일 관측되지 않은 종목을 거래하지 않고 보유 유지하는지
    (transient exclusion을 통해) 엔진 레벨(execute_simulation)에서 검증."""

    def _run(self):
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 8)
        date_range = pd.bdate_range('2024-01-01', '2024-01-08')  # Jan 1~5, 8 (주말 제외)

        a_index = date_range  # A는 매일 관측됨
        b_index = date_range[date_range != pd.Timestamp('2024-01-08')]  # B는 1/8에 결측

        a_close = pd.Series(100.0, index=a_index)
        a_close.loc[a_close.index >= pd.Timestamp('2024-01-08')] = 150.0  # 1/8 A 가격 급등 (드리프트 유발)
        b_close = pd.Series(100.0, index=b_index)

        portfolio_data = {
            'AAA': pd.DataFrame({'Close': a_close.values}, index=a_index),
            'BBB': pd.DataFrame({'Close': b_close.values}, index=b_index),
        }
        dca_info = {
            'A': _stock_info('AAA', 0.4),
            'B': _stock_info('BBB', 0.3),
            'CASH': _cash_info('CASH', 0.3),
        }
        stock_amounts = {'A': 400.0, 'B': 300.0}
        amounts = {'A': 400.0, 'B': 300.0, 'CASH': 300.0}

        async def _run_sim():
            return await engine.execute_simulation(
                date_range=date_range, start_date_obj=start, end_date_obj=end,
                stock_amounts=stock_amounts, amounts=amounts, cash_amount=300.0,
                total_amount=1000.0, portfolio_data=portfolio_data, dca_info=dca_info,
                ticker_currencies={'A': 'USD', 'B': 'USD'}, exchange_rates_by_currency={},
                rebalance_frequency='weekly_1', commission=0.0,
            )

        return asyncio.run(_run_sim())

    def test_rebalance_event_does_not_trade_the_symbol_missing_data_that_day(self):
        result = self._run()
        rebalance_history = result.attrs['rebalance_history']

        jan8_events = [e for e in rebalance_history if e['date'] == '2024-01-08']
        assert jan8_events, f"2024-01-08에 리밸런싱 이벤트가 있어야 함: {rebalance_history}"
        event = jan8_events[0]

        traded_symbols = {t['symbol'] for t in event['trades']}
        assert 'BBB' not in traded_symbols, (
            f"BBB는 2024-01-08에 원본 데이터가 없으므로 리밸런싱 거래 대상이 되면 안 됨. "
            f"실제 거래된 종목: {traded_symbols}"
        )
        # 리밸런싱 메커니즘 자체는 살아 있어야 한다 (다른 자산은 거래됨).
        assert traded_symbols, "AAA/CASH 등 관측 가능한 자산 사이의 리밸런싱은 정상 발생해야 함"


class TestValuationMarksToLastKnownPriceOnNonObservedDates:
    """평가(valuation)는 관측되지 않은 날에도 ffill된 마지막 가격으로 계속되어야
    한다 (거래만 막혀야지, 평가까지 끊기면 안 된다)."""

    def test_flat_price_mixed_market_reports_zero_return_through_the_gap(self):
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        date_range = pd.bdate_range('2024-01-01', '2024-01-10')

        a_index = date_range
        b_index = date_range[date_range != pd.Timestamp('2024-01-05')]  # B, 1/5 결측

        portfolio_data = {
            'AAA': pd.DataFrame({'Close': [100.0] * len(a_index)}, index=a_index),
            'BBB': pd.DataFrame({'Close': [100.0] * len(b_index)}, index=b_index),
        }
        dca_info = {'A': _stock_info('AAA', 0.5), 'B': _stock_info('BBB', 0.5)}
        stock_amounts = {'A': 500.0, 'B': 500.0}
        amounts = {'A': 500.0, 'B': 500.0}

        async def _run_sim():
            return await engine.execute_simulation(
                date_range=date_range, start_date_obj=start, end_date_obj=end,
                stock_amounts=stock_amounts, amounts=amounts, cash_amount=0.0,
                total_amount=1000.0, portfolio_data=portfolio_data, dca_info=dca_info,
                ticker_currencies={'A': 'USD', 'B': 'USD'}, exchange_rates_by_currency={},
                rebalance_frequency='none', commission=0.0,
            )

        result = asyncio.run(_run_sim())

        # 가격이 전혀 움직이지 않으므로(마지막 관측가로 계속 마킹), 결측일을
        # 포함해 전 구간의 일간 수익률이 0이어야 한다 -- B가 "사라진 것처럼"
        # 취급되어 그 날 포트폴리오 가치가 뚝 떨어지는 일이 없어야 한다.
        gap_day_return = result.loc[pd.Timestamp('2024-01-05'), 'Daily_Return']
        next_day_return = result.loc[pd.Timestamp('2024-01-08'), 'Daily_Return']
        assert gap_day_return == pytest.approx(0.0, abs=1e-9), (
            f"결측일의 일간 수익률: {gap_day_return} (기대: 0.0 -- 마지막 관측가로 평가되어야 함)"
        )
        assert next_day_return == pytest.approx(0.0, abs=1e-9), (
            f"결측일 다음날 수익률: {next_day_return} (기대: 0.0 -- 결측일에 사라진 것처럼 "
            f"처리됐다면 여기서 반등하는 스파이크가 생겼을 것)"
        )
        assert result['Cumulative_Return'].iloc[-1] == pytest.approx(0.0, abs=1e-6)


class TestPeriodicPurchaseDoesNotDoubleFireOnCatchUpDay:
    """장기간 지연된 초기 매수가, 그 시점에 이미 도래해 있던 정기 매수 트리거와
    같은 날 겹쳐 이중 집행되지 않는지 확인 (레벨 기반 트리거 + last_dca_date
    앵커링의 부작용 검증)."""

    def test_initial_purchase_delayed_past_first_periodic_target_fires_only_once(self):
        engine = PortfolioSimulationEngine()
        dca_manager = PortfolioDcaManager()

        start = datetime(2024, 1, 1)  # 월요일, 1월의 1번째 월요일
        date_range = pd.bdate_range('2024-01-01', '2024-04-30')

        # A는 항상 관측됨(합집합 date_range를 채우기 위한 동반 종목).
        a_index = date_range
        # C는 2024-03-01부터 데이터 시작 -- monthly_1의 첫 정기 예정일
        # (2024-02-05, 2월의 1번째 월요일)을 이미 지난 시점.
        c_index = date_range[date_range >= pd.Timestamp('2024-03-01')]

        portfolio_data = {
            'AAA': pd.DataFrame({'Close': [100.0] * len(a_index)}, index=a_index),
            'CCC': pd.DataFrame({'Close': [10.0] * len(c_index)}, index=c_index),
        }
        dca_info = {
            'A': _stock_info('AAA', 0.5),
            'C': _stock_info('CCC', 0.5, investment_type='dca', monthly_amount=1000.0,
                              dca_frequency='monthly_1', dca_periods=5),
        }
        stock_amounts = {'A': 1000.0, 'C': 1000.0}

        aligned_prices, aligned_rates = engine._pre_calculate_prices(
            date_range=date_range, stock_amounts=stock_amounts, portfolio_data=portfolio_data,
            dca_info=dca_info, ticker_currencies={'A': 'USD', 'C': 'USD'}, exchange_rates_by_currency={},
        )
        aligned_tradeable = engine._pre_calculate_tradeable_mask(
            date_range=date_range, stock_amounts=stock_amounts,
            portfolio_data=portfolio_data, dca_info=dca_info,
        )

        shares = {'A': 0.0, 'C': 0.0}
        pending = {'A', 'C'}
        last_valid_exchange_rates = {}
        prev_date = None
        c_purchase_dates = []
        executed_count_after_first_observed_day = None

        for current_date in date_range:
            current_prices, last_valid_exchange_rates = engine._get_daily_prices_from_aligned(
                current_date=current_date, aligned_prices=aligned_prices, aligned_exchange_rates=aligned_rates,
                ticker_currencies={'A': 'USD', 'C': 'USD'}, last_valid_exchange_rates=last_valid_exchange_rates,
            )
            tradeable_today = engine._get_daily_tradeable_keys(current_date, aligned_tradeable)

            before = shares['C']
            if pending:
                dca_manager.execute_initial_purchases(
                    current_date=current_date, stock_amounts=stock_amounts, current_prices=current_prices,
                    dca_info=dca_info, shares=shares, commission=0.0, pending_keys=pending,
                    tradeable_keys=tradeable_today,
                )
            if prev_date is not None and prev_date != current_date:
                dca_manager.execute_periodic_purchases(
                    current_date=current_date, stock_amounts=stock_amounts,
                    current_prices=current_prices, dca_info=dca_info, shares=shares, commission=0.0,
                    start_date_obj=start, tradeable_keys=tradeable_today,
                )
            if shares['C'] != before:
                c_purchase_dates.append(current_date.date())
                if current_date.date() == date(2024, 3, 1):
                    executed_count_after_first_observed_day = dca_info['C'].executed_count

            prev_date = current_date

        # 핵심 주장: C의 첫 관측일(2024-03-01, 지연된 초기 매수)에는 정확히
        # 1건만 집행되어야 한다 -- 그날 이미 도래해 있던 2월분 정기 매수 트리거와
        # 겹쳐 이중 집행되면 안 된다.
        assert c_purchase_dates[0] == date(2024, 3, 1)
        assert executed_count_after_first_observed_day == 1, (
            f"2024-03-01 처리 직후 executed_count={executed_count_after_first_observed_day} "
            f"(기대: 1 -- 지연된 초기 매수와 이미 도래해 있던 정기 매수가 같은 날 겹쳐 "
            f"이중 집행되면 2가 됨)"
        )
        # 같은 날짜에 두 번 집행된 적이 없어야 한다 (날짜 중복 없음).
        assert len(c_purchase_dates) == len(set(c_purchase_dates)), (
            f"같은 날짜에 두 번 매수가 잡힌 흔적이 있음: {c_purchase_dates}"
        )
        # 이후의 정기 매수(예: 4월분)는 정상적으로 별도 날짜에 집행되는 것이
        # 맞다 -- 이 테스트가 막는 것은 "같은 날 이중 집행"이지, "이후 정기
        # 매수 자체"가 아니다.
        assert len(c_purchase_dates) >= 2, (
            f"3/1 이후에도 남은 회차(dca_periods=5)가 정상적으로 이어져야 한다: {c_purchase_dates}"
        )
