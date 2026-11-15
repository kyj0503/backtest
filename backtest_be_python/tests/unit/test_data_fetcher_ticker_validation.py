"""티커 블록리스트 서브스트링 오매치 + 다운로드-후-검증 순서 회귀 테스트 (P3-22a)

버그 1 (서브스트링 오매치): DataFetcher._validate_and_clean_data()의 블록리스트
검사는 `any(pattern in ticker.upper() for pattern in invalid_patterns)` — 즉
부분 문자열 포함 여부였다. 이 때문에 블록 토큰 'ZZZ'를 부분 문자열로 포함하는
합법적인 실제 티커(캐나다 토론토 증권거래소 접미사가 붙은 'ZZZ.TO' 등)까지
InvalidSymbolError로 오차단되었다.

버그 2 (검증 순서): 이 형식 검증은 _fetch_with_retries()(실제 yfinance 네트워크
다운로드, 최대 3회 재시도) *이후*에 호출되었다. 애초에 거부되어야 할 티커에
대해서도 불필요한 네트워크 요청이 먼저 발생한 것이다.

수정:
1. 블록리스트 매치를 부분 문자열 포함이 아닌 (대소문자 무시) 정확한 일치로 변경.
2. 티커 형식 검증(_validate_ticker_symbol)을 새 메서드로 분리해
   _fetch_with_retries() 호출 이전으로 이동.
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock
import pandas as pd

from app.core.exceptions import InvalidSymbolError
from app.utils.data_fetcher import DataFetcher


pytestmark = pytest.mark.unit


@pytest.fixture
def fetcher():
    return DataFetcher()


class TestTickerBlocklistExactMatch:
    def test_legit_ticker_containing_blocked_substring_is_accepted(self, fetcher):
        """'ZZZ.TO'는 블록 토큰 'ZZZ'를 부분 문자열로 포함하지만, 그 자체로는
        블록리스트의 어떤 토큰과도 정확히 일치하지 않으므로 형식 검증을
        통과해야 한다."""
        fetcher._validate_ticker_symbol('ZZZ.TO')  # 예외가 발생하지 않아야 함

    def test_bare_blocked_token_is_still_rejected(self, fetcher):
        """블록 토큰 자체(티커 전체와 정확히 일치)는 여전히 거부되어야 한다."""
        with pytest.raises(InvalidSymbolError):
            fetcher._validate_ticker_symbol('ZZZ')

    @pytest.mark.parametrize(
        'blocked',
        ['INVALID', 'NONEXISTENT', 'NOTFOUND', 'TEST', 'FAKE', 'XXX', 'YYY', 'ZZZ'],
    )
    def test_all_known_placeholder_tokens_still_rejected_exactly(self, fetcher, blocked):
        with pytest.raises(InvalidSymbolError):
            fetcher._validate_ticker_symbol(blocked)

    def test_case_insensitive_exact_match_still_blocks(self, fetcher):
        with pytest.raises(InvalidSymbolError):
            fetcher._validate_ticker_symbol('zzz')


class TestValidationRunsBeforeDownload:
    def test_blocked_ticker_triggers_no_network_download(self, fetcher):
        """블록된 티커는 yfinance 네트워크 호출 이전에 거부되어야 한다."""
        with patch('app.utils.data_fetcher.yf') as mock_yf:
            with pytest.raises(InvalidSymbolError):
                fetcher.fetch_stock_data(
                    ticker='ZZZ',
                    start_date=date(2023, 1, 1),
                    end_date=date(2023, 2, 1),
                )

            mock_yf.Ticker.assert_not_called()
            mock_yf.download.assert_not_called()

    def test_valid_ticker_with_blocked_substring_completes_successfully(self, fetcher):
        """'ZZZ.TO'는 형식 검증에서 막히지 않고 실제로 다운로드 단계까지
        진행되어 정상적으로 데이터를 반환해야 한다."""
        with patch('app.utils.data_fetcher.yf') as mock_yf:
            mock_stock = MagicMock()
            mock_yf.Ticker.return_value = mock_stock

            dates = pd.date_range('2023-01-01', periods=10, freq='D')
            valid_df = pd.DataFrame(
                {
                    'Open': [10.0] * 10,
                    'High': [11.0] * 10,
                    'Low': [9.0] * 10,
                    'Close': [10.5] * 10,
                    'Volume': [1000] * 10,
                },
                index=dates,
            )
            mock_stock.history.return_value = valid_df

            result = fetcher.fetch_stock_data(
                ticker='ZZZ.TO',
                start_date=date(2023, 1, 1),
                end_date=date(2023, 1, 10),
            )

            assert not result.empty
            mock_yf.Ticker.assert_called_with('ZZZ.TO')
