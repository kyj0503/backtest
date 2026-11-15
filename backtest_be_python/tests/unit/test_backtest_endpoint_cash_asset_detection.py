"""
포트폴리오 백테스트 엔드포인트의 현금 자산 판별(P2-09) 회귀 테스트

**버그**:
app/api/v1/endpoints/backtest.py의 run_portfolio_backtest()는 티커 조회 대상
symbols 목록을 만들 때 `item.symbol.upper() not in ['CASH', '현금']`로 현금
항목을 걸러냈다. asset_type='cash'이지만 심볼이 "예금"처럼 그 두 리터럴과
다른 커스텀 이름이면 이 필터를 통과하지 못하고(=제외되지 않고) symbols 목록에
그대로 들어가, 존재하지도 않는 "티커"로 상장일 조회(get_tickers_info_batch)와
이후 yfinance 조회(재시도 sleep 포함)까지 흘러들어간다.

FE가 오늘 항상 symbol="CASH"만 보내서 이 버그를 가려왔을 뿐, 계약상
asset_type='cash' + 임의의 symbol/custom_name 조합이 막혀있지 않다 (배치5
항목1의 PortfolioStock 필드 순서 버그 수정으로 "예금" 같은 한글 이름도 스키마
검증을 통과하게 됐으므로 이 버그가 실제로 도달 가능해졌다).

**수정**: 문자열 화이트리스트 대신 asset_type == 'cash'로 판별한다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.unit

client = TestClient(app)


def _mock_stock_repository() -> MagicMock:
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


def _mock_success_response():
    success_result = {
        "status": "success",
        "data": {"portfolio_statistics": {}, "individual_returns": {}},
    }
    unified_data = {
        "sp500_benchmark": [],
        "nasdaq_benchmark": [],
        "exchange_rates": {},
        "latest_news": [],
    }
    return patch(
        "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
        new=AsyncMock(return_value=success_result),
    ), patch(
        "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
        return_value=unified_data,
    )


class TestCashAssetDetectedByAssetTypeNotSymbolString:
    def test_cash_item_with_custom_name_never_reaches_ticker_lookup(self):
        """RED(수정 전): asset_type='cash'인 "예금"이 symbol 문자열 화이트리스트
        (['CASH', '현금'])에 없어 티커 조회 대상에 그대로 포함됐다."""
        repo = _mock_stock_repository()
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
                {"symbol": "예금", "amount": 3000.0, "asset_type": "cash"},
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
        }
        patch_success_1, patch_success_2 = _mock_success_response()
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=repo,
        ), patch_success_1, patch_success_2:
            response = client.post("/api/v1/backtest", json=payload)

        assert response.status_code == 200, response.text
        assert repo.get_tickers_info_batch.called, "get_tickers_info_batch가 호출되지 않음"
        called_symbols = repo.get_tickers_info_batch.call_args[0][0]
        assert "예금" not in called_symbols, (
            f"현금 항목 '예금'이 티커 조회 대상에 포함됨: {called_symbols}"
        )
        assert set(called_symbols) == {"AAPL"}

    def test_literal_cash_symbol_still_excluded(self):
        """회귀 방지: symbol='CASH'(기존 관례)도 여전히 제외된다."""
        repo = _mock_stock_repository()
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
                {"symbol": "CASH", "amount": 3000.0, "asset_type": "cash"},
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
        }
        patch_success_1, patch_success_2 = _mock_success_response()
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=repo,
        ), patch_success_1, patch_success_2:
            response = client.post("/api/v1/backtest", json=payload)

        assert response.status_code == 200, response.text
        called_symbols = repo.get_tickers_info_batch.call_args[0][0]
        assert set(called_symbols) == {"AAPL"}

    def test_stock_item_named_like_cash_word_is_not_accidentally_excluded(self):
        """회귀 방지: asset_type='stock'인데 우연히 이름이 'CASH'인 경우는 없지만
        (스키마가 CASH를 특수 심볼로 취급), 일반 주식 심볼들은 asset_type
        기준으로 정확히 포함되어야 한다."""
        repo = _mock_stock_repository()
        payload = {
            "portfolio": [
                {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
                {"symbol": "MSFT", "amount": 3000.0, "asset_type": "stock"},
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
        }
        patch_success_1, patch_success_2 = _mock_success_response()
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=repo,
        ), patch_success_1, patch_success_2:
            response = client.post("/api/v1/backtest", json=payload)

        assert response.status_code == 200, response.text
        called_symbols = repo.get_tickers_info_batch.call_args[0][0]
        assert set(called_symbols) == {"AAPL", "MSFT"}
