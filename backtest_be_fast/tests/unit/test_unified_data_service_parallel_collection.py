"""unified_data_service.collect_all_unified_data 병렬화 및 중복 조회 제거
회귀 테스트 (P2-12)

collect_all_unified_data()는 모듈 docstring이 "병렬 요청으로 응답 시간을
최적화"한다고 주장하지만 실제로는 완전히 순차적이었고, 게다가 각 심볼의
주가 히스토리를 collect_stock_data()와 collect_volatility_events()가 각각
한 번씩 총 두 번 조회했다.

수정:
  (a) 심볼별 주가 히스토리를 한 번만 조회하고 두 소비자가 공유한다.
  (b) 서로 독립적인 I/O(심볼별 주가, 종목 메타데이터, 환율, 벤치마크, 뉴스)를
      bounded ThreadPoolExecutor로 병렬 실행한다 (외부 API 레이트리밋을
      존중하기 위해 워커 수를 제한한다 - 무제한 fan-out 금지).

이 테스트는 DB/네트워크를 사용하지 않는다 - data_service.get_ticker_data_sync와
stock_repo를 완전히 대체(monkeypatch)한다.
"""
import threading
import time

import pandas as pd
import pytest
from unittest.mock import MagicMock

from app.services.unified_data_service import UnifiedDataService


pytestmark = pytest.mark.unit


def _sample_price_df():
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 99.0],
            "High": [102.0, 103.0, 100.0],
            "Low": [99.0, 100.0, 98.0],
            "Close": [101.0, 99.0, 99.5],
            "Volume": [1000, 1100, 900],
        },
        index=pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03"]),
    )


@pytest.fixture
def service():
    svc = UnifiedDataService()
    # DB를 완전히 배제 - ticker_info 배치 조회를 목으로 대체
    svc.stock_repo = MagicMock()
    svc.stock_repo.get_tickers_info_batch.return_value = {}
    return svc


class TestPriceHistoryLoadedOncePerSymbol:
    """오늘의 버그: collect_stock_data와 collect_volatility_events가 심볼당
    각각 한 번씩, 총 두 번 동일한 주가 히스토리를 조회한다."""

    def test_price_loader_called_exactly_once_per_symbol(self, service, monkeypatch):
        call_log = []
        lock = threading.Lock()

        def fake_get_ticker_data_sync(ticker, start_date, end_date, use_db_first=True):
            with lock:
                call_log.append(ticker)
            return _sample_price_df()

        monkeypatch.setattr(
            "app.services.unified_data_service.data_service.get_ticker_data_sync",
            fake_get_ticker_data_sync,
        )

        result = service.collect_all_unified_data(
            symbols=["AAPL", "MSFT"],
            start_date="2023-01-01",
            end_date="2023-01-03",
            include_news=False,
        )

        symbol_calls = [c for c in call_log if c in ("AAPL", "MSFT")]
        assert symbol_calls.count("AAPL") == 1, symbol_calls
        assert symbol_calls.count("MSFT") == 1, symbol_calls

        # 공유된 데이터가 두 소비자 모두에 정확히 반영되어야 한다 (동작 보존)
        assert result["stock_data"]["AAPL"], "stock_data가 비어있음"
        assert len(result["stock_data"]["AAPL"]) == 3
        assert "AAPL" in result["volatility_events"]
        assert "MSFT" in result["volatility_events"]


class TestIndependentIOIsParallelized:
    """N개 심볼의 주가 히스토리 조회가 순차가 아니라 동시에 이루어져야 한다."""

    def test_n_symbols_are_fetched_concurrently_not_sequentially(
        self, service, monkeypatch
    ):
        SLEEP_SECONDS = 0.15
        symbols = [f"SYM{i}" for i in range(5)]

        def slow_fake(ticker, start_date, end_date, use_db_first=True):
            time.sleep(SLEEP_SECONDS)
            return _sample_price_df()

        monkeypatch.setattr(
            "app.services.unified_data_service.data_service.get_ticker_data_sync",
            slow_fake,
        )

        start = time.monotonic()
        service.collect_all_unified_data(
            symbols=symbols,
            start_date="2023-01-01",
            end_date="2023-01-03",
            include_news=False,
        )
        elapsed = time.monotonic() - start

        # 오늘(순차 + 중복): collect_stock_data에서 심볼마다 한 번(5*0.15s)
        # + collect_volatility_events에서 또 한 번(5*0.15s) + exchange(0.15s)
        # + benchmark(2*0.15s) ~= 1.95s.
        # 수정 후: 심볼 조회는 병렬 + 1회로 공유되고, exchange/benchmark/
        # ticker_info도 별도 워커에서 동시에 실행되므로 N * SLEEP_SECONDS보다
        # 충분히("well under") 작아야 한다.
        bound = len(symbols) * SLEEP_SECONDS
        assert elapsed < bound, (
            f"elapsed={elapsed:.3f}s, bound(N*sleep)={bound:.3f}s "
            "(순차 실행이거나 중복 조회가 남아있을 가능성)"
        )


class TestFullPipelineShapeIsPreservedWithNews:
    """뉴스 포함 경로까지 포함해 반환 딕셔너리 형태가 리팩터링 후에도
    유지되는지 확인 (회귀 방지)."""

    def test_return_shape_unchanged_with_news_included(self, service, monkeypatch):
        monkeypatch.setattr(
            "app.services.unified_data_service.data_service.get_ticker_data_sync",
            lambda ticker, start_date, end_date, use_db_first=True: _sample_price_df(),
        )
        service.stock_repo.load_ticker_news.return_value = []
        service.stock_repo.save_ticker_news.return_value = None

        fake_news_service = MagicMock()
        fake_news_service.get_ticker_query.return_value = "애플 주식"
        fake_news_service.search_news.return_value = [
            {"title": "뉴스", "link": "http://x", "description": "d", "pubDate": "..."}
        ]
        service.news_service = fake_news_service

        result = service.collect_all_unified_data(
            symbols=["AAPL"],
            start_date="2023-01-01",
            end_date="2023-01-03",
            include_news=True,
            news_display_count=5,
        )

        assert set(result.keys()) == {
            "ticker_info",
            "stock_data",
            "exchange_rates",
            "exchange_stats",
            "volatility_events",
            "sp500_benchmark",
            "nasdaq_benchmark",
            "latest_news",
        }
        assert result["latest_news"]["AAPL"][0]["title"] == "뉴스"
