"""
심볼/티커 검증 로직

**역할**:
- 티커 심볼 형식 검증
- 티커 존재 여부 확인
- 심볼 정규화 (대문자 변환 등)

**주요 기능**:
1. validate_ticker_format(): 티커 형식 검증
2. validate_ticker_exists(): 티커 존재 여부 확인
3. normalize_ticker(): 티커 정규화

**검증 규칙**:
- 1~10자 길이
- 영문자, 숫자, 하이픈(-), 점(.) 허용
- 대문자로 정규화

**사용 예**:
```python
from app.validators.symbol_validator import SymbolValidator

validator = SymbolValidator(data_fetcher)
ticker = validator.normalize_ticker("aapl")  # "AAPL"
validator.validate_ticker_format(ticker)
validator.validate_ticker_exists(ticker)
```
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class SymbolValidator:
    """티커 심볼 검증 전담 클래스"""

    # 티커 형식 정규식: 영문자, 숫자, 하이픈, 점 허용
    TICKER_PATTERN = re.compile(r'^[A-Z0-9.\-]{1,10}$')

    def __init__(self, data_fetcher=None):
        """
        Args:
            data_fetcher: 티커 존재 여부 확인을 위한 DataFetcher 인스턴스 (선택)
        """
        self.data_fetcher = data_fetcher

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        """
        티커를 정규화 (대문자 변환, 공백 제거)

        Args:
            ticker: 정규화할 티커

        Returns:
            정규화된 티커

        Examples:
            >>> validator = SymbolValidator()
            >>> validator.normalize_ticker("aapl")
            'AAPL'
            >>> validator.normalize_ticker(" msft ")
            'MSFT'
        """
        if not ticker:
            raise ValueError("티커가 비어있습니다")

        normalized = ticker.strip().upper()
        logger.debug(f"티커 정규화: {ticker} -> {normalized}")
        return normalized

    def validate_ticker_format(self, ticker: str) -> None:
        """
        티커 형식 검증

        Args:
            ticker: 검증할 티커 (정규화된 상태여야 함)

        Raises:
            ValueError: 티커 형식이 유효하지 않은 경우

        Examples:
            >>> validator = SymbolValidator()
            >>> validator.validate_ticker_format("AAPL")  # OK
            >>> validator.validate_ticker_format("INVALID_TICKER")  # ValueError
        """
        if not ticker:
            raise ValueError("티커가 비어있습니다")

        if not isinstance(ticker, str):
            raise ValueError(f"티커는 문자열이어야 합니다: {type(ticker)}")

        if len(ticker) > 10:
            raise ValueError(f"티커가 너무 깁니다: {ticker} ({len(ticker)}자, 최대 10자)")

        if not self.TICKER_PATTERN.match(ticker):
            raise ValueError(
                f"유효하지 않은 티커 형식입니다: {ticker} "
                f"(영문자, 숫자, '.', '-'만 허용)"
            )

        logger.debug(f"티커 형식 검증 통과: {ticker}")

    def validate_ticker_exists(self, ticker: str) -> None:
        """
        티커 존재 여부 확인 (DataFetcher 필요)

        Args:
            ticker: 확인할 티커

        Raises:
            ValueError: DataFetcher가 없거나 티커가 존재하지 않는 경우

        Examples:
            >>> from app.utils.data_fetcher import data_fetcher
            >>> validator = SymbolValidator(data_fetcher)
            >>> validator.validate_ticker_exists("AAPL")  # OK if exists
        """
        if not self.data_fetcher:
            logger.warning("DataFetcher가 설정되지 않아 티커 존재 여부를 확인할 수 없습니다")
            return

        try:
            if not self.data_fetcher.validate_ticker(ticker):
                raise ValueError(f"존재하지 않는 티커입니다: {ticker}")

            logger.debug(f"티커 존재 확인 통과: {ticker}")

        except Exception as e:
            logger.error(f"티커 존재 확인 실패: {ticker}, {str(e)}")
            raise ValueError(f"티커 확인 중 오류 발생: {ticker}")

    def validate_and_normalize(self, ticker: str) -> str:
        """
        티커 정규화 및 검증 (올인원 메서드)

        Args:
            ticker: 검증 및 정규화할 티커

        Returns:
            정규화된 티커

        Raises:
            ValueError: 검증 실패 시

        Examples:
            >>> validator = SymbolValidator()
            >>> ticker = validator.validate_and_normalize("aapl")
            >>> print(ticker)
            'AAPL'
        """
        # 1. 정규화
        normalized = self.normalize_ticker(ticker)

        # 2. 형식 검증
        self.validate_ticker_format(normalized)

        # 3. 존재 여부 확인 (DataFetcher가 있는 경우)
        if self.data_fetcher:
            self.validate_ticker_exists(normalized)

        return normalized
