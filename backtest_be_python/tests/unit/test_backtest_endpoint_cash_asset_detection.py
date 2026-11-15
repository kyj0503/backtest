"""
포트폴리오 백테스트 엔드포인트의 현금 자산 판별(P2-09) 회귀 테스트

현금 항목은 symbol 문자열이 아니라 asset_type == 'cash'로 판별한다. "예금" 같은 커스텀 이름의
현금 항목이 시세 조회 대상(티커)으로 흘러들어가면 안 된다.
"""
from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.engine.marketdata import Bar, History
from app.engine.source import Loaded
from app.main import app

pytestmark = pytest.mark.unit

client = TestClient(app)


def _flat(symbol: str) -> History:
    start, end = date(2023, 1, 1).toordinal(), date(2023, 6, 30).toordinal()
    return History(symbol=symbol, bars=[Bar(d, 100.0, 100.0, 100.0, 100.0) for d in range(start, end + 1)])


def _post(portfolio):
    calls = []

    def load(symbols, start, end):
        calls.append(list(symbols))
        return Loaded(histories={s: _flat(s) for s in symbols})

    payload = {
        "portfolio": portfolio,
        "start_date": "2023-01-01",
        "end_date": "2023-06-30",
        "strategy": "buy_hold_strategy",
    }
    with patch("app.engine.service.source.load", side_effect=load), \
            patch("app.engine.service.attach", lambda req, data, loaded: None):
        response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, response.text
    assert len(calls) == 1
    return calls[0], response.json()


class TestCashAssetDetectedByAssetTypeNotSymbolString:
    def test_cash_item_with_custom_name_never_reaches_ticker_lookup(self):
        symbols, body = _post([
            {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
            {"symbol": "예금", "amount": 3000.0, "asset_type": "cash"},
        ])
        assert symbols == ["AAPL"]
        assert "예금__cash_2" in body["data"]["individual_returns"]

    def test_literal_cash_symbol_still_excluded(self):
        symbols, body = _post([
            {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
            {"symbol": "CASH", "amount": 3000.0, "asset_type": "cash"},
        ])
        assert symbols == ["AAPL"]
        assert "CASH__cash_2" in body["data"]["individual_returns"]

    def test_stock_symbols_are_all_requested(self):
        symbols, _ = _post([
            {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
            {"symbol": "MSFT", "amount": 3000.0, "asset_type": "stock"},
        ])
        assert symbols == ["AAPL", "MSFT"]
