"""협력적 취소 토큰과 실행 경로의 취소 지점 회귀 테스트 (A-05)

타임아웃 뒤 작업이 "설정 시간 안에 실제로 멈추려면" 스레드 안의 긴 구간
(시뮬레이션 일별 루프, 외부 수집 재시도 대기, 병렬 수집 스레드)이 취소 신호를
확인해야 한다. 여기서는 그 지점들이 실제로 신호를 보고 멈추는지 검증한다.
"""
import concurrent.futures
import time
from datetime import datetime
from unittest.mock import Mock

import pandas as pd
import pytest

from app.core.cancellation import (
    BacktestCancelled,
    CancelToken,
    bind_token,
    cancellable_sleep,
    check_cancelled,
    current_token,
    submit_with_context,
)

pytestmark = pytest.mark.unit


class TestCancelToken:
    def test_check_is_noop_without_token(self):
        check_cancelled()  # 예외 없음

    def test_cancel_raises_at_next_check(self):
        token = CancelToken()
        with bind_token(token):
            check_cancelled()
            token.cancel("timeout")
            with pytest.raises(BacktestCancelled) as exc:
                check_cancelled()
        assert exc.value.reason == "timeout"

    def test_cancellation_is_not_swallowed_by_except_exception(self):
        """실행 경로의 `except Exception:`(종목별 실패 건너뛰기, 재시도)에 삼켜지면
        취소가 '한 종목 실패'로 둔갑해 작업이 계속 돈다."""
        token = CancelToken()
        token.cancel("timeout")
        with bind_token(token):
            with pytest.raises(BacktestCancelled):
                try:
                    check_cancelled()
                except Exception:  # noqa: BLE001 — 의도적으로 넓게 잡는다
                    pytest.fail("BacktestCancelled가 except Exception에 잡혔다")

    def test_cancellable_sleep_wakes_up_immediately_on_cancel(self):
        token = CancelToken()
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        with bind_token(token):
            future = submit_with_context(pool, cancellable_sleep, 5.0)
        time.sleep(0.05)
        start = time.monotonic()
        token.cancel("timeout")
        with pytest.raises(BacktestCancelled):
            future.result(timeout=2)
        assert time.monotonic() - start < 0.5
        pool.shutdown()

    def test_callbacks_run_once_even_if_registered_after_cancel(self):
        token = CancelToken()
        calls = []
        token.add_callback(lambda: calls.append("before"))
        token.cancel("a")
        token.cancel("b")
        token.add_callback(lambda: calls.append("after"))
        assert calls == ["before", "after"]
        assert token.reason == "a"

    def test_plain_executor_submit_does_not_see_token_but_helper_does(self):
        """ThreadPoolExecutor.submit은 컨텍스트를 복사하지 않는다 — 그래서
        submit_with_context가 필요하다."""
        token = CancelToken()
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=2)
        with bind_token(token):
            plain = pool.submit(current_token).result()
            helped = submit_with_context(pool, current_token).result()
        pool.shutdown()
        assert plain is None
        assert helped is token


class TestSimulationLoopStopsOnCancel:
    def test_daily_loop_checks_the_token(self):
        from app.domain.portfolio_domain import DcaStrategyInfo
        from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine

        engine = PortfolioSimulationEngine()
        start, end = datetime(2015, 1, 1), datetime(2024, 12, 31)
        date_range = pd.bdate_range(start=start, end=end)
        prices = pd.DataFrame({"Close": [100.0] * len(date_range)}, index=date_range)
        dca_info = {
            "A": DcaStrategyInfo(
                symbol="AAA", allocation=1.0, asset_type="stock",
                investment_type="lump_sum", monthly_amount=0.0,
            ),
        }
        seen_days = []
        original = engine._get_daily_prices_from_aligned

        def spy(*args, **kwargs):
            seen_days.append(kwargs.get("current_date"))
            if len(seen_days) == 50:
                token.cancel("timeout")
            return original(*args, **kwargs)

        engine._get_daily_prices_from_aligned = spy
        token = CancelToken()
        with bind_token(token):
            with pytest.raises(BacktestCancelled):
                engine._execute_simulation_sync(
                    date_range, start, end, {"A": 1000.0}, {"A": 1000.0}, 0.0, 1000.0,
                    {"AAA": prices}, dca_info, {"A": "USD"}, {}, "none", 0.0,
                )
        assert len(seen_days) <= 51, f"취소 후에도 {len(seen_days)}일을 더 돌았다"


class TestExternalCollectionStopsOnCancel:
    def test_load_ticker_data_does_not_sleep_through_retries_after_cancel(self, monkeypatch):
        """DB 로드 실패 → 2초·4초 백오프 재시도. 취소되면 대기 도중 즉시 멈춘다."""
        from app.repositories.yfinance_repository import YFinanceRepository

        repo = YFinanceRepository()
        token = CancelToken()
        attempts = []

        def failing(*args, **kwargs):
            attempts.append(1)
            token.cancel("timeout")  # 첫 시도 실패 직후 취소가 들어온 상황
            raise RuntimeError("transient DB error")

        monkeypatch.setattr(repo, "_load_ticker_data_internal", failing)
        start = time.monotonic()
        with bind_token(token):
            with pytest.raises(BacktestCancelled):
                repo.load_ticker_data("AAPL", "2023-01-01", "2023-06-30")
        assert time.monotonic() - start < 0.5, "재시도 백오프(2초)를 그대로 기다렸다"
        assert attempts == [1]

    def test_yahoo_download_attempts_stop_after_cancel(self, monkeypatch):
        """데이터가 비면 범위를 넓혀 최대 6번 다운로드를 시도한다. 취소되면 다음
        시도를 하지 않는다."""
        from app.utils import data_fetcher as data_fetcher_module

        fetcher = data_fetcher_module.DataFetcher()
        token = CancelToken()
        calls = []

        class FakeTicker:
            def history(self, **kwargs):
                calls.append("history")
                token.cancel("timeout")
                return pd.DataFrame()

        monkeypatch.setattr(data_fetcher_module.yf, "download", Mock(side_effect=AssertionError("취소 후 호출됨")))
        with bind_token(token):
            with pytest.raises(BacktestCancelled):
                fetcher._fetch_with_retries(FakeTicker(), "AAPL", "2023-01-01", "2023-06-30")
        assert calls == ["history"]

    def test_parallel_collection_threads_see_the_token(self, monkeypatch):
        """부가 데이터 병렬 수집 스레드도 취소 신호를 볼 수 있어야 한다."""
        from app.services.unified_data_service import UnifiedDataService

        svc = UnifiedDataService()
        seen = []

        def fake_fetch(symbol, start_date, end_date):
            seen.append(current_token())
            return pd.DataFrame()

        monkeypatch.setattr(svc, "_fetch_price_history", fake_fetch)
        token = CancelToken()
        with bind_token(token):
            svc._fetch_price_histories(["AAA", "BBB"], "2023-01-01", "2023-06-30")
        assert seen and all(t is token for t in seen)

    def test_news_retry_wait_is_cancellable(self):
        import inspect
        from app.services import news_service as news_module

        source = inspect.getsource(news_module)
        assert "time.sleep(" not in source, "뉴스 재시도 대기가 취소 불가능한 time.sleep이다"
