"""PortfolioManagerService 응답 스냅샷 특성화 테스트 (A-16 분리 전 고정)

A-16(대형 모듈 책임 분리)은 순수 리팩터링이어야 한다 — 응답 JSON의 키, 값,
**키 순서**가 바뀌면 안 된다. 기존 테스트는 개별 수치를 골라 검증하고, e2e 골든
마스터는 `sort_keys=True`로 저장해 키 순서를 보지 않으며 DCA 단일 종목 한 가지만
다룬다. 이 파일은 두 경로(buy&hold 시뮬레이터, 전략 합산)의 대표 분기를 합성
데이터로 돌려 응답 전체를 스냅샷과 비교한다:

- buy&hold: 일시불+DCA+같은 이름 현금 두 개+리밸런싱+수수료 / weight 모드 DCA /
  현금 전용 / 데이터 로드 실패 종목(A-03 warnings)
- 전략: amount 모드(현금 + 거래 없는 종목 + 실패 종목) / weight 모드

비교는 JSON 왕복 후 값으로 한다(클라이언트가 받는 형태). dict는 키 목록을 순서까지,
float는 1e-9 허용오차로, 그 외(int/str/bool/None)는 타입까지 완전 일치를 요구한다.

재생성(의도된 동작 변경일 때만):
    REGENERATE_PM_SNAPSHOT=1 pytest tests/unit/test_portfolio_manager_response_snapshot.py
재생성 모드는 파일을 덮어쓰고 skip한다. diff를 검토한 뒤 환경변수 없이 다시 돌려 확인한다.
"""
import asyncio
import json
import math
import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import numpy as np
import pandas as pd
import pytest

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService

pytestmark = pytest.mark.unit

SNAPSHOT_FILE = os.path.join(
    os.path.dirname(__file__), "data", "portfolio_manager_response_snapshot.json"
)
REGENERATE_ENV_VAR = "REGENERATE_PM_SNAPSHOT"

START = "2024-01-02"
END = "2024-04-30"


def _frame(seed: float, start: str = START, end: str = END, drift: float = 0.05) -> pd.DataFrame:
    """결정적 합성 가격(난수 없음). 오르내림이 있어 MDD·승률이 0이 아니게 한다."""
    index = pd.bdate_range(start=start, end=end)
    i = np.arange(len(index))
    close = 100.0 + seed * np.sin(i / 4.0) + drift * i
    return pd.DataFrame({"Close": close}, index=index)


def _fx_rates() -> dict:
    """통화별 {date: rate}. KRW는 1달러당 원(나눗셈), EUR는 1유로당 달러(곱셈)."""
    days = pd.date_range(START, END, freq="D")
    return {
        "KRW": {d.date(): 1300.0 + 2.0 * (k % 11) for k, d in enumerate(days)},
        "EUR": {d.date(): 1.08 + 0.001 * (k % 7) for k, d in enumerate(days)},
    }


def _request(portfolio, **overrides) -> PortfolioBacktestRequest:
    params = dict(
        portfolio=portfolio,
        start_date=START,
        end_date=END,
        commission=0.0,
        rebalance_frequency="none",
        strategy="buy_hold_strategy",
    )
    params.update(overrides)
    return PortfolioBacktestRequest(**params)


def _run_buy_hold(request: PortfolioBacktestRequest, frames: dict,
                  currencies: dict = None, rates: dict = None) -> dict:
    service = PortfolioManagerService()
    currencies = currencies or {symbol: "USD" for symbol in frames}
    with patch.object(
        service.data_loader, "load_stock_data_parallel", new=AsyncMock(return_value=frames)
    ), patch.object(
        service.data_loader, "load_ticker_currencies", new=AsyncMock(return_value=currencies),
    ), patch.object(
        service.data_loader, "load_exchange_rates", new=AsyncMock(return_value=rates or {})
    ):
        return asyncio.run(service.run_portfolio_backtest(request))


def _strategy_result(frame: pd.DataFrame, amount: float, *, total_trades: int,
                     win_rate_pct: float, sharpe: float, mdd: float) -> SimpleNamespace:
    shares = amount / frame["Close"].iloc[0]
    equity_curve = {
        d.strftime("%Y-%m-%d"): float(shares * price) for d, price in frame["Close"].items()
    }
    return SimpleNamespace(
        final_equity=float(shares * frame["Close"].iloc[-1]),
        equity_curve=equity_curve,
        total_trades=total_trades,
        win_rate_pct=win_rate_pct,
        max_drawdown_pct=mdd,
        sharpe_ratio=sharpe,
    )


def _run_strategy(request: PortfolioBacktestRequest, results_by_symbol: dict) -> dict:
    async def fake_run_backtest(backtest_req):
        value = results_by_symbol[backtest_req.ticker]
        if isinstance(value, Exception):
            raise value
        # initial_cash가 amount/weight 환산 결과대로 넘어오는지도 스냅샷에 남긴다
        return value(backtest_req.initial_cash) if callable(value) else value

    service = PortfolioManagerService()
    with patch(
        "app.services.portfolio_manager_service.backtest_service.run_backtest",
        new=AsyncMock(side_effect=fake_run_backtest),
    ):
        return asyncio.run(service.run_portfolio_backtest(request))


def _scenarios() -> dict:
    aapl = _frame(8.0)
    msft = _frame(5.0, drift=-0.03)
    nvda = _frame(12.0, drift=0.2)

    return {
        "buy_hold_mixed_rebalance": lambda: _run_buy_hold(
            _request(
                [
                    {"symbol": "AAPL", "amount": 5000.0},
                    {"symbol": "MSFT", "amount": 500.0, "investment_type": "dca",
                     "dca_frequency": "monthly_1"},
                    {"symbol": "예금", "amount": 1000.0, "asset_type": "cash"},
                    {"symbol": "예금", "amount": 500.0, "asset_type": "cash"},
                ],
                commission=0.001,
                rebalance_frequency="monthly_1",
            ),
            {"AAPL": aapl, "MSFT": msft},
        ),
        "buy_hold_weight_dca": lambda: _run_buy_hold(
            _request(
                [
                    {"symbol": "AAPL", "weight": 60.0, "investment_type": "dca",
                     "dca_frequency": "weekly_2"},
                    {"symbol": "NVDA", "weight": 40.0},
                ],
                commission=0.002,
            ),
            {"AAPL": aapl, "NVDA": nvda},
        ),
        "buy_hold_fx_rebalance": lambda: _run_buy_hold(
            _request(
                [
                    {"symbol": "005930.KS", "amount": 4000.0},
                    {"symbol": "SAP", "amount": 3000.0},
                    {"symbol": "AAPL", "amount": 3000.0},
                ],
                commission=0.001,
                rebalance_frequency="weekly_2",
            ),
            {"005930.KS": _frame(3000.0, drift=40.0) + 70000.0, "SAP": _frame(6.0), "AAPL": aapl},
            currencies={"005930.KS": "KRW", "SAP": "EUR", "AAPL": "USD"},
            rates=_fx_rates(),
        ),
        "buy_hold_cash_only": lambda: _run_buy_hold(
            _request([{"symbol": "CASH", "amount": 2500.0, "asset_type": "cash"}]),
            {},
        ),
        "buy_hold_failed_symbol": lambda: _run_buy_hold(
            _request(
                [
                    {"symbol": "AAPL", "amount": 3000.0},
                    {"symbol": "ZZZZ", "amount": 3000.0},
                    {"symbol": "CASH", "amount": 1000.0, "asset_type": "cash"},
                ],
            ),
            {"AAPL": aapl},
        ),
        "strategy_amount_mixed": lambda: _run_strategy(
            _request(
                [
                    {"symbol": "AAPL", "amount": 6000.0},
                    {"symbol": "MSFT", "amount": 3000.0},
                    {"symbol": "NVDA", "amount": 2000.0},
                    {"symbol": "현금", "amount": 1000.0, "asset_type": "cash"},
                ],
                strategy="sma_strategy",
                rebalance_frequency="none",
                commission=0.001,
            ),
            {
                "AAPL": _strategy_result(aapl, 6000.0, total_trades=4, win_rate_pct=75.0,
                                         sharpe=1.2, mdd=-8.5),
                "MSFT": _strategy_result(msft, 3000.0, total_trades=0, win_rate_pct=0.0,
                                         sharpe=0.0, mdd=-3.0),
                "NVDA": RuntimeError("synthetic failure"),
            },
        ),
        "strategy_weight": lambda: _run_strategy(
            _request(
                [
                    {"symbol": "AAPL", "weight": 55.0},
                    {"symbol": "NVDA", "weight": 47.0},
                ],
                strategy="rsi_strategy",
                rebalance_frequency="none",
            ),
            {
                "AAPL": lambda cash: _strategy_result(aapl, cash, total_trades=3,
                                                      win_rate_pct=33.3333333, sharpe=0.4,
                                                      mdd=-12.0),
                "NVDA": lambda cash: _strategy_result(nvda, cash, total_trades=2,
                                                      win_rate_pct=100.0, sharpe=2.1,
                                                      mdd=-4.0),
            },
        ),
    }


def _to_client_json(result):
    return json.loads(json.dumps(result, ensure_ascii=False))


def _assert_same(actual, expected, path):
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: dict가 아님 ({type(actual).__name__})"
        assert list(actual.keys()) == list(expected.keys()), (
            f"{path}: 키 목록/순서 불일치\n actual={list(actual.keys())}\n expected={list(expected.keys())}"
        )
        for key in expected:
            _assert_same(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: list가 아님 ({type(actual).__name__})"
        assert len(actual) == len(expected), (
            f"{path}: 길이 불일치 actual={len(actual)} expected={len(expected)}"
        )
        for i, (a, e) in enumerate(zip(actual, expected)):
            _assert_same(a, e, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert type(actual) is float, f"{path}: float가 아님 (actual={actual!r})"
        assert math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9), (
            f"{path}: 값 불일치 actual={actual!r} expected={expected!r}"
        )
    else:
        assert type(actual) is type(expected) and actual == expected, (
            f"{path}: 값/타입 불일치 actual={actual!r} expected={expected!r}"
        )


def _load_snapshot() -> dict:
    with open(SNAPSHOT_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def snapshot():
    if os.environ.get(REGENERATE_ENV_VAR) == "1":
        data = {name: _to_client_json(run()) for name, run in _scenarios().items()}
        os.makedirs(os.path.dirname(SNAPSHOT_FILE), exist_ok=True)
        with open(SNAPSHOT_FILE, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
            f.write("\n")
        pytest.skip(f"{REGENERATE_ENV_VAR}=1: 스냅샷을 재생성했습니다 ({SNAPSHOT_FILE})")
    return _load_snapshot()


@pytest.mark.parametrize("name", list(_scenarios().keys()))
def test_response_matches_snapshot(name, snapshot):
    actual = _to_client_json(_scenarios()[name]())
    _assert_same(actual, snapshot[name], name)


def test_snapshot_covers_every_scenario(snapshot):
    assert list(snapshot.keys()) == list(_scenarios().keys())
