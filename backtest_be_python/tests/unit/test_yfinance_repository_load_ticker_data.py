"""load_ticker_data 재시도 정책 회귀 테스트 (P2-11)

YFinanceRepository.load_ticker_data()는 _load_ticker_data_internal()이 빈
DataFrame을 반환하는 경우(= 해당 티커/기간에 데이터가 없는 정상적인 결과)를
일시적 장애와 동일하게 취급해 2초, 4초 대기 후 동일 쿼리를 최대 3회 재시도하고,
최종적으로 맨 ValueError를 발생시켰다. 두 가지 문제가 있었다:
  (a) 빈 심볼 하나당 약 6초의 불필요한 지연이 발생한다.
  (b) 맨 ValueError는 BacktestEngine.run_backtest()에서 HTTP 500으로 매핑되는데,
      "이 티커/기간에 데이터 없음"은 404에 해당하는 조건이다.

수정: 빈 결과는 재시도 없이 즉시 DataNotFoundError(404)를 발생시킨다. 네트워크/DB
오류 등 "진짜" 예외에 대한 재시도+백오프 동작은 그대로 유지한다 (load-bearing).

이 테스트는 _load_ticker_data_internal()을 목(mock)하여 DB/네트워크 없이 순수하게
재시도 정책만 검증한다.
"""
import pandas as pd
import pytest
from unittest.mock import Mock

from app.core.exceptions import DataNotFoundError
from app.repositories.yfinance_repository import YFinanceRepository


pytestmark = pytest.mark.unit


@pytest.fixture
def repository():
    """YFinanceRepository 인스턴스 (DB/네트워크 미사용, _load_ticker_data_internal만 목킹)"""
    return YFinanceRepository()


@pytest.fixture
def patch_sleep(monkeypatch):
    """time.sleep을 무력화해 재시도 테스트를 빠르게 유지 (백오프 자체는 별도로 검증)"""
    mock_sleep = Mock()
    monkeypatch.setattr(
        "app.repositories.yfinance_repository.time.sleep", mock_sleep
    )
    return mock_sleep


class TestEmptyResultFailsFastWithoutRetry:
    """빈 결과는 일시적 장애가 아니므로 재시도 없이 즉시 404급 예외를 내야 한다"""

    def test_empty_dataframe_raises_data_not_found_error(
        self, repository, patch_sleep, monkeypatch
    ):
        mock_internal = Mock(return_value=pd.DataFrame())
        monkeypatch.setattr(repository, "_load_ticker_data_internal", mock_internal)

        with pytest.raises(DataNotFoundError):
            repository.load_ticker_data("NODATA", "2023-01-01", "2023-01-31")

    def test_empty_dataframe_calls_internal_loader_exactly_once(
        self, repository, patch_sleep, monkeypatch
    ):
        """재시도가 없다는 것을 직접 증명 - 오늘의 버그는 3회 호출 + ~6초 대기였다."""
        mock_internal = Mock(return_value=pd.DataFrame())
        monkeypatch.setattr(repository, "_load_ticker_data_internal", mock_internal)

        with pytest.raises(DataNotFoundError):
            repository.load_ticker_data("NODATA", "2023-01-01", "2023-01-31")

        assert mock_internal.call_count == 1
        patch_sleep.assert_not_called()


class TestGenuineExceptionsStillRetryWithBackoff:
    """네트워크/DB 오류 등 진짜 예외에 대한 재시도+백오프는 그대로 유지되어야 한다"""

    def test_transient_exception_twice_then_success_returns_data(
        self, repository, patch_sleep, monkeypatch
    ):
        sample_df = pd.DataFrame({"Close": [100.0, 101.0]})
        mock_internal = Mock(
            side_effect=[
                ConnectionError("일시적 네트워크 오류"),
                ConnectionError("일시적 네트워크 오류"),
                sample_df,
            ]
        )
        monkeypatch.setattr(repository, "_load_ticker_data_internal", mock_internal)

        result = repository.load_ticker_data("AAPL", "2023-01-01", "2023-01-31")

        pd.testing.assert_frame_equal(result, sample_df)
        assert mock_internal.call_count == 3
        # 재시도 사이 2회 대기(1회차->2회차, 2회차->3회차)했어야 한다
        assert patch_sleep.call_count == 2

    def test_persistent_genuine_exception_raises_after_max_retries(
        self, repository, patch_sleep, monkeypatch
    ):
        mock_internal = Mock(side_effect=ConnectionError("DB 연결 실패"))
        monkeypatch.setattr(repository, "_load_ticker_data_internal", mock_internal)

        with pytest.raises(ValueError):
            repository.load_ticker_data(
                "AAPL", "2023-01-01", "2023-01-31", max_retries=3
            )

        assert mock_internal.call_count == 3
