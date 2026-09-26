"""
백테스트 요청의 단계별 소요 시간 계측 회귀 테스트 (A-08 계측)

**배경**: POST /api/v1/backtest 한 요청이 시뮬레이션뿐 아니라 종목 메타데이터,
원본 주가, 환율, 변동성 이벤트, 벤치마크 지수, 뉴스까지 수집한다. 어느 단계가
실제 병목인지 모른 채 분리하면 병목이 아닌 곳을 자를 수 있으므로, 먼저 단계별
소요 시간을 Prometheus 히스토그램(backtest_stage_duration_seconds{stage})과
요청당 요약 로그 한 줄로 남긴다.

이 테스트는 DB/네트워크를 쓰지 않는다.
"""
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest
from prometheus_client import REGISTRY

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.services.unified_data_service import UnifiedDataService

pytestmark = pytest.mark.unit

SUPPLEMENTAL_STAGES = (
    "ticker_info",
    "price_history",
    "exchange_rates",
    "benchmarks",
    "news",
    "stock_data",
    "volatility_events",
    "supplemental_total",
)


def _stage_count(stage: str) -> float:
    value = REGISTRY.get_sample_value(
        "backtest_stage_duration_seconds_count", {"stage": stage}
    )
    return value or 0.0


def _sample_price_df():
    return pd.DataFrame(
        {"Close": [101.0, 99.0, 99.5], "Volume": [1000, 1100, 900]},
        index=pd.to_datetime(["2023-01-02", "2023-01-03", "2023-01-04"]),
    )


@pytest.fixture
def service(monkeypatch):
    svc = UnifiedDataService()
    svc.stock_repo = MagicMock()
    svc.stock_repo.get_tickers_info_batch.return_value = {}
    svc.stock_repo.load_ticker_news.return_value = [{"title": "cached"}]
    svc.news_service = MagicMock()
    monkeypatch.setattr(
        "app.services.unified_data_service.data_service.get_ticker_data_sync",
        lambda ticker, start_date, end_date, use_db_first=True: _sample_price_df(),
    )
    return svc


class TestSupplementalStagesAreTimed:
    def test_every_supplemental_stage_is_observed_once_per_request(self, service):
        """RED(수정 전): backtest_stage_duration_seconds 메트릭이 없어 모든
        stage의 count가 0에서 늘지 않는다."""
        before = {stage: _stage_count(stage) for stage in SUPPLEMENTAL_STAGES}

        service.collect_all_unified_data(
            symbols=["AAPL", "MSFT"],
            start_date="2023-01-01",
            end_date="2023-01-05",
            include_news=True,
            news_display_count=5,
        )

        for stage in SUPPLEMENTAL_STAGES:
            assert _stage_count(stage) == before[stage] + 1, (
                f"stage={stage}가 요청당 정확히 1회 관측되지 않음"
            )

    def test_one_summary_log_line_lists_stage_timings(self, service, caplog):
        with caplog.at_level(logging.INFO, logger="app.services.unified_data_service"):
            service.collect_all_unified_data(
                symbols=["AAPL"],
                start_date="2023-01-01",
                end_date="2023-01-05",
                include_news=True,
            )

        summary = [r.getMessage() for r in caplog.records if "단계별 소요" in r.getMessage()]
        assert len(summary) == 1, summary
        for stage in SUPPLEMENTAL_STAGES:
            assert f"{stage}=" in summary[0], (stage, summary[0])


class TestSimulationStageIsTimed:
    def test_buy_and_hold_simulation_observes_simulation_stage(self):
        before = _stage_count("simulation")

        index = pd.bdate_range("2024-01-01", "2024-03-29")
        frames = {"AAPL": pd.DataFrame({"Close": [100.0] * len(index)}, index=index)}
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAPL", "amount": 10000.0}],
            start_date="2024-01-01",
            end_date="2024-03-29",
            commission=0.0,
            rebalance_frequency="none",
            strategy="buy_hold_strategy",
        )
        service = PortfolioManagerService()
        with patch.object(
            service.data_loader, "load_stock_data_parallel", new=AsyncMock(return_value=frames)
        ), patch.object(
            service.data_loader, "load_ticker_currencies", new=AsyncMock(return_value={"AAPL": "USD"})
        ), patch.object(
            service.data_loader, "load_exchange_rates", new=AsyncMock(return_value={})
        ):
            result = asyncio.run(service.run_buy_and_hold_portfolio_backtest(request))

        assert result["status"] == "success"
        assert _stage_count("simulation") == before + 1
