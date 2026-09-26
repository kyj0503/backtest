"""
단일 백테스트 응답의 부가 데이터 결합 완화 회귀 테스트 (A-08)

**문제**: POST /api/v1/backtest는 시뮬레이션 결과에 원본 주가, 급등락 이벤트,
환율, S&P 500/NASDAQ, 뉴스를 항상 붙여 반환했다. 로컬 실측(HISTORY 참고)에서
부가 데이터는 응답 바이트의 67~74%, 요청 시간의 약 60%(p50)를 차지했다.
- 필요 없는 호출자도 끌 수 없었다.
- 부가 수집이 느리면(외부 API 지연) 핵심 결과까지 함께 늦어지고, 전체 요청
  타임아웃에 걸리면 핵심 결과까지 잃었다.
- collect_all_unified_data()가 예상 못 한 예외를 던지면 요청 전체가 500이었다.

**수정 (하위 호환)**:
- 요청에 include_stock_data / include_volatility_events / include_exchange_rates /
  include_benchmarks / include_news를 추가한다. 기본값은 모두 True — 기존
  호출자(FE)는 아무것도 바꾸지 않아도 같은 응답을 받는다.
- 부가 수집에 시간 예산(supplemental_data_timeout_seconds)을 둔다. 예산 안에
  끝나지 않은 섹션은 비워서 반환하고 나머지는 그대로 돌려준다.
- 섹션별 결과를 supplemental_status(ok/empty/skipped/timeout/error)로 응답에
  싣고, backtest_supplemental_outcome_total{section,outcome}로 센다.
- 부가 수집 전체가 예외로 실패해도 핵심 결과는 200으로 반환한다.
"""
import threading
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.unified_data_service import UnifiedDataService

pytestmark = pytest.mark.unit

client = TestClient(app)

LEGACY_KEYS = {
    "ticker_info",
    "stock_data",
    "exchange_rates",
    "exchange_stats",
    "volatility_events",
    "sp500_benchmark",
    "nasdaq_benchmark",
    "latest_news",
}


def _price_df():
    return pd.DataFrame(
        {"Close": [100.0, 110.0, 99.0], "Volume": [1, 2, 3]},
        index=pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"]),
    )


@pytest.fixture
def service(monkeypatch):
    svc = UnifiedDataService()
    svc.stock_repo = MagicMock()
    svc.stock_repo.get_tickers_info_batch.return_value = {"AAPL": {"currency": "USD"}}
    svc.stock_repo.load_ticker_news.return_value = [{"title": "cached"}]
    svc.news_service = MagicMock()
    monkeypatch.setattr(
        "app.services.unified_data_service.data_service.get_ticker_data_sync",
        lambda ticker, start_date, end_date, use_db_first=True: _price_df(),
    )
    return svc


def _outcome_count(section: str, outcome: str) -> float:
    value = REGISTRY.get_sample_value(
        "backtest_supplemental_outcome_total", {"section": section, "outcome": outcome}
    )
    return value or 0.0


class TestRequestOptionsDefaultToCurrentBehaviour:
    def test_all_include_flags_default_to_true(self):
        """RED(수정 전): 필드가 없어 AttributeError."""
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
            start_date="2023-01-01",
            end_date="2023-06-30",
        )
        assert request.include_stock_data is True
        assert request.include_volatility_events is True
        assert request.include_exchange_rates is True
        assert request.include_benchmarks is True
        assert request.include_news is True

    def test_default_collection_keeps_every_legacy_key_populated(self, service):
        result = service.collect_all_unified_data(
            symbols=["AAPL"], start_date="2023-01-01", end_date="2023-01-05"
        )
        assert LEGACY_KEYS <= set(result.keys())
        assert result["stock_data"]["AAPL"]
        assert result["sp500_benchmark"]
        assert result["exchange_rates"]
        assert result["latest_news"]["AAPL"]
        assert result["supplemental_status"] == {
            "ticker_info": "ok",
            "stock_data": "ok",
            "volatility_events": "ok",
            "exchange_rates": "ok",
            "benchmarks": "ok",
            "news": "ok",
        }


class TestExcludedSectionsAreNotCollected:
    def test_excluded_sections_skip_their_io_and_keep_keys_empty(self, service, monkeypatch):
        fetched = []
        lock = threading.Lock()

        def tracking_fetch(ticker, start_date, end_date, use_db_first=True):
            with lock:
                fetched.append(ticker)
            return _price_df()

        monkeypatch.setattr(
            "app.services.unified_data_service.data_service.get_ticker_data_sync",
            tracking_fetch,
        )

        result = service.collect_all_unified_data(
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-01-05",
            include_stock_data=False,
            include_volatility_events=False,
            include_exchange_rates=False,
            include_benchmarks=False,
            include_news=False,
        )

        assert fetched == [], f"끈 섹션의 외부 조회가 실행됨: {fetched}"
        service.stock_repo.load_ticker_news.assert_not_called()
        # 키는 남기고 값만 비운다 — 응답 형태를 기대하는 호출자가 깨지지 않도록
        assert LEGACY_KEYS <= set(result.keys())
        assert result["stock_data"] == {}
        assert result["volatility_events"] == {}
        assert result["exchange_rates"] == []
        assert result["exchange_stats"] == {}
        assert result["sp500_benchmark"] == []
        assert result["nasdaq_benchmark"] == []
        assert result["latest_news"] == {}
        assert result["ticker_info"] == {"AAPL": {"currency": "USD"}}
        status = result["supplemental_status"]
        assert status.pop("ticker_info") == "ok"
        assert set(status.values()) == {"skipped"}

    def test_volatility_events_alone_still_fetches_prices(self, service):
        result = service.collect_all_unified_data(
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-01-05",
            include_stock_data=False,
            include_news=False,
        )
        assert result["stock_data"] == {}
        assert result["volatility_events"]["AAPL"], "급등락 이벤트가 계산되지 않음"
        assert result["supplemental_status"]["stock_data"] == "skipped"
        assert result["supplemental_status"]["volatility_events"] == "ok"


class TestSlowSupplementalDoesNotBlockTheRest:
    def test_section_over_budget_is_emptied_and_others_are_returned(self, service, monkeypatch):
        release = threading.Event()

        def slow_benchmarks(start_date, end_date, fill_missing_dates=True):
            release.wait(5)
            return [{"date": "2023-01-02", "close": 1.0, "return_pct": 0.0}], []

        monkeypatch.setattr(service, "collect_benchmark_data", slow_benchmarks)
        before = _outcome_count("benchmarks", "timeout")
        try:
            started = time.monotonic()
            result = service.collect_all_unified_data(
                symbols=["AAPL"],
                start_date="2023-01-01",
                end_date="2023-01-05",
                timeout_seconds=0.3,
            )
            elapsed = time.monotonic() - started
        finally:
            release.set()

        assert elapsed < 2.0, f"느린 섹션을 끝까지 기다렸다 ({elapsed:.2f}s)"
        assert result["sp500_benchmark"] == []
        assert result["nasdaq_benchmark"] == []
        assert result["supplemental_status"]["benchmarks"] == "timeout"
        assert result["stock_data"]["AAPL"], "시간 안에 끝난 섹션까지 버려졌다"
        assert result["supplemental_status"]["stock_data"] == "ok"
        assert _outcome_count("benchmarks", "timeout") == before + 1

    def test_unexpected_exception_in_one_section_is_contained(self, service, monkeypatch):
        def broken_exchange(start_date, end_date):
            raise RuntimeError("boom")

        monkeypatch.setattr(service, "collect_exchange_data", broken_exchange)
        result = service.collect_all_unified_data(
            symbols=["AAPL"], start_date="2023-01-01", end_date="2023-01-05"
        )
        assert result["exchange_rates"] == []
        assert result["exchange_stats"] == {}
        assert result["supplemental_status"]["exchange_rates"] == "error"
        assert result["supplemental_status"]["benchmarks"] == "ok"

    def test_completed_but_empty_section_is_reported_as_empty(self, service, monkeypatch):
        """외부 API 실패는 수집기 안에서 삼켜져 빈 값으로 돌아온다 — 'ok'와
        구분해야 외부 장애를 지표로 볼 수 있다."""
        monkeypatch.setattr(
            service, "collect_benchmark_data", lambda start_date, end_date, fill_missing_dates=True: ([], [])
        )
        before = _outcome_count("benchmarks", "empty")
        result = service.collect_all_unified_data(
            symbols=["AAPL"], start_date="2023-01-01", end_date="2023-01-05"
        )
        assert result["supplemental_status"]["benchmarks"] == "empty"
        assert _outcome_count("benchmarks", "empty") == before + 1


def _mock_stock_repository() -> MagicMock:
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


def _core_result():
    return {
        "status": "success",
        "data": {"portfolio_statistics": {"Total_Return": 12.5}, "individual_returns": {}},
    }


PAYLOAD = {
    "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
    "start_date": "2023-01-01",
    "end_date": "2023-06-30",
    "strategy": "buy_hold_strategy",
}


class TestEndpointPassesOptionsAndProtectsCoreResult:
    def test_request_flags_reach_the_collector(self):
        collector = MagicMock(return_value={})
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=_mock_stock_repository(),
        ), patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(return_value=_core_result()),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            collector,
        ):
            response = client.post(
                "/api/v1/backtest",
                json=dict(PAYLOAD, include_news=False, include_benchmarks=False),
            )

        assert response.status_code == 200, response.text
        kwargs = collector.call_args.kwargs
        assert kwargs["include_news"] is False
        assert kwargs["include_benchmarks"] is False
        assert kwargs["include_stock_data"] is True
        assert kwargs["include_volatility_events"] is True
        assert kwargs["include_exchange_rates"] is True
        assert kwargs["timeout_seconds"] > 0

    def test_collector_crash_still_returns_core_result(self):
        """RED(수정 전): 부가 수집 예외가 그대로 전파되어 500."""
        with patch(
            "app.api.v1.endpoints.backtest.get_stock_repository",
            return_value=_mock_stock_repository(),
        ), patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(return_value=_core_result()),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            side_effect=RuntimeError("collector exploded"),
        ):
            response = client.post("/api/v1/backtest", json=PAYLOAD)

        assert response.status_code == 200, response.text
        data = response.json()["data"]
        assert data["portfolio_statistics"]["Total_Return"] == 12.5
        assert LEGACY_KEYS <= set(data.keys())
        assert set(data["supplemental_status"].values()) == {"error"}
