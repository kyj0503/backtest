"""PortfolioManagerService 배치4 버그 수정 회귀 테스트 (fix/audit-batch4)

**테스트 범위**:
- BUG P1-04 (buy&hold weight 모드 미구현): run_buy_and_hold_portfolio_backtest에서
  item.weight만 입력된 경우 per_period_amount가 0으로 고정되어 total_amount=0이 되고,
  포트폴리오 시뮬레이션(정규화 단계)에서 0으로 나누기가 발생해 요청이 크래시한다.
  STRATEGY 경로(run_strategy_portfolio_backtest)가 이미 사용 중인 "100 단위 환산"
  규칙을 buy&hold 경로에도 동일하게 적용해야 한다.
- BUG P2-07 (중복 현금 항목의 amounts 딕셔너리 키 충돌): schemas.py의 중복 종목
  검증은 asset_type == 'cash' 항목을 의도적으로 예외 처리하지만(같은 이름의 현금을
  여러 개 추가할 수 있음), run_buy_and_hold_portfolio_backtest는 amounts[symbol]에
  덮어쓰기로 저장하면서 cash_amount는 누적하므로 total_amount(=sum(amounts.values()))가
  실제 현금 총액보다 작아지고, individual_returns['CASH']의 weight/amount와
  불일치한다.
- BUG P2-08 (전략 포트폴리오 통계가 근사치): run_strategy_portfolio_backtest가
  보고하는 Sharpe_Ratio/Max_Drawdown/Avg_Drawdown/Peak_Value/Total_Trading_Days는
  개별 종목 지표의 가중평균이거나 최종값 재활용이지, 실제 포트폴리오 전체의
  지표가 아니다(종목 간 상관관계, 시점 차이를 무시함). 이미 계산되는 집계
  equity_curve/daily_returns로부터 진짜 포트폴리오 지표를 도출해야 한다.

각 버그는 먼저 실패하는 테스트(RED)로 재현한 뒤 구현을 수정해 통과(GREEN)시키는
TDD 절차를 따른다.
"""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService

pytestmark = pytest.mark.unit

FLAT_PRICE = 100.0


# ---------------------------------------------------------------------------
# Buy & Hold 헬퍼 (test_dca_schedule_alignment.py와 동일한 패턴)
# ---------------------------------------------------------------------------

def _flat_price_frame(start: str, end: str, price: float = FLAT_PRICE) -> pd.DataFrame:
    """영업일 기준 고정 가격 프레임 (가격이 변하지 않으므로 수익률은 0이어야 한다)."""
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


def _run_buy_hold(request: PortfolioBacktestRequest, frames: dict) -> dict:
    """stock_repository를 mock한 채 buy&hold 포트폴리오 백테스트를 실행한다."""
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


class TestBuyHoldWeightModeIsImplemented:
    """P1-04: buy&hold 경로에서 weight 모드가 0으로 나누기 없이 동작해야 한다.

    수정 전: item.weight만 입력되면 per_period_amount = 0 (TODO로 남겨진 채
    처리되지 않음) -> total_investment = 0 -> total_amount = 0 -> 시뮬레이션의
    정규화 단계(normalized_value = current_portfolio_value / total_amount)에서
    ZeroDivisionError가 발생해 요청이 크래시한다 (스키마상 유효한 요청인데도).
    """

    def test_single_item_weight_100_succeeds_with_zero_return_on_flat_market(self):
        """단일 종목 weight=100(amount 없음), flat 가격, 수수료 0 -> 성공 + 총수익률 0%.

        수정 전에는 ZeroDivisionError로 크래시한다(오늘은 500).
        """
        start, end = '2024-01-01', '2024-06-30'
        request = PortfolioBacktestRequest(
            portfolio=[{'symbol': 'AAPL', 'weight': 100}],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_buy_hold(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)

    def test_two_item_weights_60_40_report_zero_return_on_flat_market(self):
        """2종목 weight=60/40(합계 100%), flat 가격 -> 총수익률 0%.

        weight가 100 단위 기준으로 올바르게 금액 환산되어야 두 종목의 투자금
        비율이 6:4로 유지되고, total_amount가 두 종목 합산 금액과 일치한다.
        """
        start, end = '2024-01-01', '2024-06-30'
        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAA', 'weight': 60},
                {'symbol': 'BBB', 'weight': 40},
            ],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_buy_hold(request, {
            'AAA': _flat_price_frame(start, end),
            'BBB': _flat_price_frame(start, end),
        })

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)

    def test_weight_mode_with_dca_still_returns_zero_on_flat_market(self):
        """weight 모드 + DCA 조합에서도 (per_period_amount = 환산총액/dca_periods)
        분모가 총 투자금과 재계산 시 일치해야 총수익률이 0%로 나온다."""
        start, end = '2024-01-01', '2024-12-31'
        request = PortfolioBacktestRequest(
            portfolio=[{
                'symbol': 'AAPL',
                'weight': 100,
                'investment_type': 'dca',
                'dca_frequency': 'monthly_1',
            }],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_buy_hold(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)

    def test_amount_mode_regression_guard(self):
        """회귀 방지: amount 모드는 이번 weight 모드 수정의 영향을 받지 않아야 한다."""
        start, end = '2024-01-01', '2024-06-30'
        request = PortfolioBacktestRequest(
            portfolio=[{'symbol': 'AAPL', 'amount': 10000.0}],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_buy_hold(request, {'AAPL': _flat_price_frame(start, end)})

        assert _total_return(result) == pytest.approx(0.0, abs=1e-6)
        assert _final_value(result) == pytest.approx(10000.0, abs=1e-6)


class TestDuplicateCashEntriesAreTrackedIndependently:
    """P2-07: 이름이 같은 현금 항목이 여러 개 있어도 total_amount와 개별 현금
    항목의 weight/amount가 일치해야 한다.

    주의: 순수 현금만 있는 포트폴리오(주식 0개)는 run_buy_and_hold_portfolio_backtest
    안의 "현금만 있는 경우" 조기 반환 분기를 타는데, 그 분기는 cash_amount를 직접
    사용하고 버그가 있는 total_amount(=sum(amounts.values()))를 아예 읽지 않으므로
    우연히 이 버그를 드러내지 않는다. 버그를 실제로 관측하려면 total_amount가 실제로
    쓰이는 "주식 포함" 경로를 거쳐야 하므로, 아래 테스트는 주식 1종목을 포함한다.
    """

    def test_duplicate_cash_symbols_keep_independent_totals_with_stock(self):
        """AAPL(1000, 주식) + CASH(500) + CASH(300) -> 총 투자금 1800, CASH 비중 800/1800.

        수정 전 실측값: Initial_Value=1300 (CASH 500이 dict 키 충돌로 유실),
        individual_returns['CASH']['weight']=800/1300≈0.6154 (>1300 분모라서 왜곡),
        weight 합계 ≈1.3846 (100%를 초과).
        """
        start, end = '2024-01-01', '2024-06-30'
        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAPL', 'amount': 1000.0},
                {'symbol': 'CASH', 'amount': 500.0, 'asset_type': 'cash'},
                {'symbol': 'CASH', 'amount': 300.0, 'asset_type': 'cash'},
            ],
            start_date=start,
            end_date=end,
            commission=0.0,
            rebalance_frequency='none',
            strategy='buy_hold_strategy',
        )

        result = _run_buy_hold(request, {'AAPL': _flat_price_frame(start, end)})

        assert result['status'] == 'success', result
        data = result['data']
        stats = data['portfolio_statistics']
        cash_entry = data['individual_returns']['CASH']

        # 총 투자금: AAPL 1000 + CASH 500 + CASH 300 = 1800
        assert stats['Initial_Value'] == pytest.approx(1800.0), (
            f"Initial_Value={stats['Initial_Value']} (기대: 1800.0) -- "
            f"중복 현금 항목의 amounts 딕셔너리 키 충돌로 500이 유실된 것으로 의심됨"
        )

        # CASH 개별 투자금은 두 항목의 합(800)이어야 한다.
        assert cash_entry['amount'] == pytest.approx(800.0)

        # weight는 진짜 총 투자금(1800) 기준이어야 한다.
        assert cash_entry['weight'] == pytest.approx(800.0 / 1800.0, abs=1e-9), (
            f"CASH weight={cash_entry['weight']} (기대: {800.0/1800.0:.6f})"
        )

        # 전체 비중 합은 100%여야 한다 (분모가 틀리면 100%를 넘어선다).
        total_weight = sum(r['weight'] for r in data['individual_returns'].values())
        assert total_weight == pytest.approx(1.0, abs=1e-6), (
            f"individual_returns 비중 합계={total_weight} (기대: 1.0)"
        )


# ---------------------------------------------------------------------------
# 전략 포트폴리오(run_strategy_portfolio_backtest) 헬퍼
# ---------------------------------------------------------------------------

def _make_backtest_side_effect(equity_curves: dict, sharpe_by_symbol: dict, mdd_by_symbol: dict):
    """symbol별 결정론적 equity_curve를 반환하는 backtest_service.run_backtest 대역."""

    def _side_effect(backtest_req):
        symbol = backtest_req.ticker
        curve = equity_curves[symbol]
        last_date = sorted(curve.keys())[-1]
        return SimpleNamespace(
            final_equity=curve[last_date],
            total_trades=0,
            win_rate_pct=0.0,
            max_drawdown_pct=mdd_by_symbol.get(symbol, 0.0),
            sharpe_ratio=sharpe_by_symbol.get(symbol, 0.0),
            equity_curve=curve,
        )

    return _side_effect


@pytest.mark.asyncio
class TestStrategyPortfolioTrueMetrics:
    """P2-08: 전략 포트폴리오 통계는 집계된 equity curve에서 유도한 실제 값이어야
    하며, 종목별 지표의 가중평균(상관관계 무시)이어서는 안 된다.
    """

    async def test_non_overlapping_drawdowns_yield_true_mdd_and_sharpe_smaller_than_weighted_average(
        self,
    ):
        """A는 2일차에, B는 4일차에 서로 다른 날 -20%씩 하락한다 (동시에 저점을
        찍지 않음). 포트폴리오 전체로 보면 어느 한쪽이 하락해도 다른 한쪽이
        버텨주므로 실제 포트폴리오 MDD(-10%)는 개별 MDD의 가중평균(-20%)보다
        완만해야 한다. 두 종목 모두 5일째 원금(1000)으로 복귀하므로 포트폴리오
        총수익률은 0%이고, 진짜 샤프 비율도 0이어야 한다(가중평균 샤프는 2.0으로
        보고되어 왔음 - 개별 sharpe_ratio 입력값 1.0/3.0의 단순 평균).

        수정 전 실측값(가중평균/근사식 기반):
          Max_Drawdown=-20.0, Sharpe_Ratio=2.0, Avg_Drawdown=-10.0(우연히 일치),
          Peak_Value=2000.0(Final_Value와 동일, 우연히 일치), Total_Trading_Days=4
          (달력일, 실제 데이터 포인트는 5개).
        """
        equity_curves = {
            'AAA': {
                '2024-01-01': 1000.0,
                '2024-01-02': 800.0,  # -20% 하락 (2일차)
                '2024-01-03': 1000.0,
                '2024-01-04': 1000.0,
                '2024-01-05': 1000.0,
            },
            'BBB': {
                '2024-01-01': 1000.0,
                '2024-01-02': 1000.0,
                '2024-01-03': 1000.0,
                '2024-01-04': 800.0,  # -20% 하락 (4일차, A와 다른 날)
                '2024-01-05': 1000.0,
            },
        }
        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAA', 'amount': 1000.0},
                {'symbol': 'BBB', 'amount': 1000.0},
            ],
            start_date='2024-01-01',
            end_date='2024-01-05',
            strategy='sma_strategy',
            commission=0.0,
        )

        service = PortfolioManagerService()
        side_effect = _make_backtest_side_effect(
            equity_curves,
            sharpe_by_symbol={'AAA': 1.0, 'BBB': 3.0},
            mdd_by_symbol={'AAA': -20.0, 'BBB': -20.0},
        )
        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=AsyncMock(side_effect=side_effect),
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result['status'] == 'success', result
        stats = result['data']['portfolio_statistics']

        # 진짜 포트폴리오 MDD: 두 하락이 겹치지 않으므로 -10%로, 가중평균(-20%)보다 완만함
        assert stats['Max_Drawdown'] == pytest.approx(-10.0, abs=1e-6), (
            f"Max_Drawdown={stats['Max_Drawdown']} (기대: -10.0, 가중평균 근사값은 -20.0)"
        )
        # 진짜 포트폴리오 샤프: 총수익률 0% -> 0이어야 함 (가중평균 근사값은 2.0)
        assert stats['Sharpe_Ratio'] == pytest.approx(0.0, abs=1e-9), (
            f"Sharpe_Ratio={stats['Sharpe_Ratio']} (기대: 0.0, 가중평균 근사값은 2.0)"
        )
        assert stats['Avg_Drawdown'] == pytest.approx(-10.0, abs=1e-6)
        assert stats['Peak_Value'] == pytest.approx(2000.0, abs=1e-6)
        # 실제 데이터 포인트는 5개(1/1~1/5) -- 달력일 차이(4)가 아니어야 함
        assert stats['Total_Trading_Days'] == 5, (
            f"Total_Trading_Days={stats['Total_Trading_Days']} (기대: 5, 달력일 근사값은 4)"
        )

    async def test_peak_value_reflects_true_curve_peak_not_final_value(self):
        """단일 종목이 급등 후 하락해 원금으로 복귀한다 (최종 수익률 0%).
        Peak_Value는 곡선의 실제 최고점(1500)이어야 하며, 옛 코드처럼 그냥
        Final_Value(1000)를 재활용해서는 안 된다.
        """
        equity_curves = {
            'AAA': {
                '2024-01-01': 1000.0,
                '2024-01-02': 1500.0,  # +50% 급등 (최고점)
                '2024-01-03': 1300.0,
                '2024-01-04': 1100.0,
                '2024-01-05': 1000.0,  # 원금 복귀 (총수익률 0%)
            },
        }
        request = PortfolioBacktestRequest(
            portfolio=[{'symbol': 'AAA', 'amount': 1000.0}],
            start_date='2024-01-01',
            end_date='2024-01-05',
            strategy='sma_strategy',
            commission=0.0,
        )

        service = PortfolioManagerService()
        side_effect = _make_backtest_side_effect(
            equity_curves, sharpe_by_symbol={'AAA': 0.0}, mdd_by_symbol={'AAA': 0.0}
        )
        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=AsyncMock(side_effect=side_effect),
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result['status'] == 'success', result
        stats = result['data']['portfolio_statistics']

        assert stats['Peak_Value'] == pytest.approx(1500.0, abs=1e-6), (
            f"Peak_Value={stats['Peak_Value']} (기대: 1500.0) -- "
            f"옛 코드는 Final_Value를 그대로 재활용해 1000.0을 보고했음"
        )
        assert stats['Peak_Value'] >= stats['Final_Value']

    async def test_avg_drawdown_is_the_true_mean_not_half_of_max_drawdown(self):
        """A는 서로 다른 깊이의 하락을 두 번 겪고(-10%, -30%), B는 변동이 없다.
        옛 코드의 Avg_Drawdown = -weighted_max_drawdown/2 = -(0.5*30+0.5*0)/2 = -7.5는
        "최대 낙폭의 절반"이라는 임의의 공식일 뿐, 실제 낙폭 구간(day2=-5%, day4=-15%)의
        평균(-10.0%)과 다르다.
        """
        equity_curves = {
            'AAA': {
                '2024-01-01': 1000.0,
                '2024-01-02': 900.0,   # -10% (1차 하락)
                '2024-01-03': 1000.0,  # 회복
                '2024-01-04': 700.0,   # -30% (2차, 더 깊은 하락)
                '2024-01-05': 1000.0,  # 회복
            },
            'BBB': {
                '2024-01-01': 1000.0,
                '2024-01-02': 1000.0,
                '2024-01-03': 1000.0,
                '2024-01-04': 1000.0,
                '2024-01-05': 1000.0,
            },
        }
        request = PortfolioBacktestRequest(
            portfolio=[
                {'symbol': 'AAA', 'amount': 1000.0},
                {'symbol': 'BBB', 'amount': 1000.0},
            ],
            start_date='2024-01-01',
            end_date='2024-01-05',
            strategy='sma_strategy',
            commission=0.0,
        )

        service = PortfolioManagerService()
        side_effect = _make_backtest_side_effect(
            equity_curves,
            sharpe_by_symbol={'AAA': 0.0, 'BBB': 0.0},
            mdd_by_symbol={'AAA': -30.0, 'BBB': 0.0},
        )
        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=AsyncMock(side_effect=side_effect),
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result['status'] == 'success', result
        stats = result['data']['portfolio_statistics']

        assert stats['Avg_Drawdown'] == pytest.approx(-10.0, abs=1e-6), (
            f"Avg_Drawdown={stats['Avg_Drawdown']} (기대: -10.0, "
            f"'최대낙폭/2' 근사식은 -7.5를 보고했음)"
        )
