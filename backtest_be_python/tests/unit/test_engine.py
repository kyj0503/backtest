"""app/engine (Go 엔진 이식) 단위 테스트: 예정일, 검증, 환율, 고정 시세, 계산 불변식."""
import json
from datetime import date

import pytest

from app.engine import buyhold, schedule, strategy, technical
from app.engine.errors import AppError
from app.engine.marketdata import Bar, FixtureFetcher, History, rate_on
from app.engine.request import Asset, Limits, Request, validate
from app.engine.service import run

pytestmark = pytest.mark.unit


def d(s: str) -> int:
    return date.fromisoformat(s).toordinal()


def iso(o: int) -> str:
    return date.fromordinal(o).isoformat()


def weekdays(symbol, start, end, price=lambda i: 100.0, currency="USD"):
    bars = []
    for i, o in enumerate(range(d(start), d(end) + 1)):
        if date.fromordinal(o).weekday() < 5:
            p = price(i)
            bars.append(Bar(o, p, p, p, p, 1000.0))
    return History(symbol=symbol, currency=currency, bars=bars)


LIMITS = Limits(min_period_days=30, max_period_days=3650, max_items=20, max_symbol_len=10, today=d("2026-01-01"))


class TestSchedule:
    def test_monthly_keeps_nth_weekday_and_falls_back_to_last(self):
        # 2023-01-31은 다섯째 화요일 → 다섯째가 없는 달은 마지막 화요일
        got = [iso(x) for x in schedule.dates(d("2023-01-31"), d("2023-06-30"), "monthly_1")]
        assert got == ["2023-02-28", "2023-03-28", "2023-04-25", "2023-05-30", "2023-06-27"]

    def test_weekly_and_unknown(self):
        assert [iso(x) for x in schedule.dates(d("2023-01-02"), d("2023-01-20"), "weekly_1")] == [
            "2023-01-09", "2023-01-16"]
        assert schedule.dates(d("2023-01-02"), d("2023-12-31"), "daily") == []


class TestStrategyParameters:
    def test_strings_are_numbers_and_values_truncate(self):
        assert strategy.parameters("rsi_strategy", {"rsi_period": "7.9"})["rsi_period"] == 7.0

    def test_range_and_order(self):
        with pytest.raises(AppError, match="short_window: 허용 범위는 2~50입니다."):
            strategy.parameters("sma_strategy", {"short_window": 1})
        with pytest.raises(AppError, match="short_window은 long_window보다 작아야 합니다."):
            strategy.parameters("sma_strategy", {"short_window": 30, "long_window": 20})
        with pytest.raises(AppError, match="std_dev: 허용 범위는 0.5~4입니다."):
            strategy.parameters("bollinger_strategy", {"std_dev": 0.1})


class TestValidate:
    def _req(self, *assets, **kw):
        return Request(portfolio=list(assets), start=d("2023-01-03"), end=d("2023-10-31"), **kw)

    @pytest.mark.parametrize("asset,msg", [
        (Asset("AAPL", amount=100, total_amount=50, weight=None, investment_type="dca"), None),
        (Asset("AAPL", total_amount=50), "total_amount는 amount와 함께만 사용할 수 있습니다."),
        (Asset("AAPL", amount=1e13), "금액 또는 비중이 유효하지 않습니다."),
        (Asset("AAPL", amount=1, investment_type="dca", dca_frequency="monthly_12"),
         "DCA 주기가 백테스트 기간보다 깁니다."),
    ])
    def test_item_rules(self, asset, msg):
        req = self._req(asset)
        if msg is None:
            validate(req, LIMITS)
        else:
            with pytest.raises(AppError) as e:
                validate(req, LIMITS)
            assert e.value.status == 422 and e.value.detail == msg

    def test_rebalance_default_depends_on_strategy(self):
        assert self._req(Asset("AAPL", amount=1)).rebalance() == "monthly_1"
        assert self._req(Asset("AAPL", amount=1), strategy="sma_strategy").rebalance() == "none"

    def test_symbols_are_uppercased_and_cash_ids_are_per_item(self):
        req = self._req(Asset("aapl", amount=1), Asset("CASH", amount=1, asset_type="cash"))
        validate(req, LIMITS)
        assert req.portfolio[0].symbol == "AAPL"
        assert [a.id(i) for i, a in enumerate(req.portfolio)] == ["AAPL", "CASH__cash_2"]


class TestRateOn:
    def test_forward_fill_only(self):
        fx = History(symbol="KRW=X", currency="KRW", bars=[Bar(d("2023-01-05"), 1, 1, 1, 1250.0)])
        data = {"KRW=X": fx}
        assert rate_on("KRW", d("2023-01-08"), data) == pytest.approx(1 / 1250)
        with pytest.raises(AppError, match="2023-01-04 이전의 유효한 환율이 없습니다."):
            rate_on("KRW", d("2023-01-04"), data)
        assert rate_on("USD", d("2023-01-04"), {}) == 1.0


class TestFixtures:
    def test_load_and_unknown_symbol_is_404(self, tmp_path):
        path = tmp_path / "h.json"
        path.write_text(json.dumps({"AAPL": {
            "symbol": "AAPL", "currency": "USD", "company_name": "AAPL", "exchange": "TEST",
            "first_trade_date": None,
            "bars": [{"date": "2023-01-02", "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "volume": 5}],
        }}), encoding="utf-8")
        f = FixtureFetcher.load(str(path))
        assert len(f.fetch("AAPL", d("2023-01-01"), d("2023-01-31")).bars) == 1
        with pytest.raises(AppError) as e:
            f.fetch("ZZZZ", d("2023-01-01"), d("2023-01-31"))
        assert e.value.status == 404

    def test_invalid_bar_is_rejected(self, tmp_path):
        path = tmp_path / "h.json"
        path.write_text(json.dumps({"AAPL": {"symbol": "AAPL", "bars": [
            {"date": "2023-01-02", "open": 2.0, "high": 1.0, "low": 1.0, "close": 1.0}]}}), encoding="utf-8")
        with pytest.raises(ValueError, match="invalid bar"):
            FixtureFetcher.load(str(path))

    def test_fixture_file_requires_debug(self):
        from app.core.config import Settings
        with pytest.raises(ValueError, match="only allowed with DEBUG=true"):
            Settings(_env_file=None, debug=False, backtest_fixture_file="/x.json")
        assert Settings(_env_file=None, debug=True, backtest_fixture_file="/x.json").backtest_fixture_file


class TestBuyHold:
    def test_lump_sum_buys_budget_over_one_plus_commission(self):
        data = {"AAPL": weekdays("AAPL", "2023-01-02", "2023-03-31")}
        req = Request(portfolio=[Asset("AAPL", amount=1000.0)], start=d("2023-01-02"), end=d("2023-03-31"),
                      commission=0.01, rebalance_frequency="none")
        out = run(req, data)
        s = out["portfolio_statistics"]
        assert s["Final_Value"] == pytest.approx(1000 / 1.01)
        assert s["Initial_Value"] == 1000.0
        assert s["Total_Trading_Days"] == d("2023-03-31") - d("2023-01-02") + 1
        assert len(out["equity_curve"]) == s["Total_Trading_Days"]

    def test_total_amount_dca_preserves_budget(self):
        data = {"AAPL": weekdays("AAPL", "2023-01-02", "2023-10-31")}
        req = Request(portfolio=[Asset("AAPL", amount=333.33, total_amount=3000.0, investment_type="dca")],
                      start=d("2023-01-03"), end=d("2023-10-31"), commission=0.0, rebalance_frequency="none")
        out = run(req, data)
        item = out["individual_returns"]["AAPL"]
        assert item["amount"] == pytest.approx(3000.0)
        assert item["dca_periods"] == 10

    def test_missing_symbol_is_excluded_with_warning(self):
        data = {"AAPL": weekdays("AAPL", "2023-01-02", "2023-03-31")}
        req = Request(portfolio=[Asset("AAPL", amount=1000.0), Asset("ZZZZ", amount=1234.5)],
                      start=d("2023-01-02"), end=d("2023-03-31"), rebalance_frequency="none")
        out = buyhold.run(req, data)
        assert out["warnings"] == ["종목 ZZZZ의 가격 데이터를 불러오지 못해 백테스트에서 제외했습니다 "
                                   "(투자금 $1,234.50는 수익률 계산에 포함되지 않음)."]
        assert [c["asset_id"] for c in out["portfolio_composition"]] == ["AAPL"]

    def test_dca_into_falling_stock_reports_real_drawdown(self):
        n = 300
        data = {"AAPL": weekdays("AAPL", "2023-01-02", "2023-12-29", price=lambda i: 100.0 - 40.0 * i / n)}
        req = Request(portfolio=[Asset("AAPL", amount=100.0, investment_type="dca")],
                      start=d("2023-01-02"), end=d("2023-12-29"), commission=0.0, rebalance_frequency="none")
        s = run(req, data)["portfolio_statistics"]
        assert s["Max_Drawdown"] < -30


class TestTechnical:
    def test_signal_fills_at_next_bar_open(self):
        # 하락 후 상승: SMA(2, 10) 골든 크로스가 생긴다
        prices = [100 - i for i in range(30)] + [70 + 2 * i for i in range(60)]
        data = {"AAPL": weekdays("AAPL", "2023-01-02", "2023-06-30", price=lambda i: float(prices[min(i, 89)]))}
        for b in data["AAPL"].bars:  # 시가를 종가와 다르게
            b.open = b.close + 0.5
            b.high = b.open
        req = Request(portfolio=[Asset("AAPL", amount=1000.0)], start=d("2023-01-02"), end=d("2023-06-30"),
                      strategy="sma_strategy", strategy_params={"short_window": 2, "long_window": 10})
        out = technical.run(req, data)
        detail = out["strategy_details"]["AAPL"]
        first = (detail["trade_log"] or detail["open_positions"])[0]
        bars = [b for b in data["AAPL"].bars]
        entry = next(b for b in bars if iso(b.date) == first["EntryTime"][:10])
        assert first["EntryPrice"] == entry.open
        assert out["portfolio_statistics"]["Profit_Factor"] is None or out["portfolio_statistics"]["Profit_Factor"] >= 0
