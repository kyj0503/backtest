"""class BacktestError(Exception):

통합된 예외 처리 시스템    """백테스트 관련 커스텀 예외 클래스"""

백테스트 애플리케이션의 모든 커스텀 예외를 정의합니다.    def __init__(self, message: str, code: str = "BACKTEST_ERROR"):

"""        self.message = message

from fastapi import HTTPException, status        self.code = code

from typing import Optional        super().__init__(self.message) 
import logging

logger = logging.getLogger(__name__)


# 기본 예외 클래스
class BacktestException(Exception):
    """백테스트 관련 기본 예외"""
    def __init__(self, message: str, code: str = "BACKTEST_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


# HTTP 예외 클래스들
class DataNotFoundError(HTTPException):
    """데이터를 찾을 수 없을 때 발생하는 예외"""
    def __init__(self, symbol: str, start_date: str, end_date: str):
        detail = f"'{symbol}' 종목의 데이터를 찾을 수 없습니다. (기간: {start_date} ~ {end_date})"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        logger.warning(f"데이터 없음: {symbol} ({start_date} ~ {end_date})")


class InvalidSymbolError(HTTPException):
    """잘못된 종목 심볼일 때 발생하는 예외"""
    def __init__(self, symbol: str):
        detail = f"'{symbol}'은(는) 유효하지 않은 종목 심볼입니다."
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
        logger.warning(f"잘못된 심볼: {symbol}")


class YFinanceRateLimitError(HTTPException):
    """Yahoo Finance API 제한에 도달했을 때 발생하는 예외"""
    def __init__(self, retry_after: int = 60):
        detail = f"Yahoo Finance API 요청 제한에 도달했습니다. {retry_after}초 후 다시 시도해주세요."
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )
        logger.warning("Yahoo Finance API 요청 제한 도달")


class ValidationError(HTTPException):
    """검증 실패 시 발생하는 예외"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
        logger.warning(f"검증 실패: {message}")


# 유틸리티 함수
def handle_yfinance_error(error: Exception, symbol: str, start_date: str, end_date: str) -> HTTPException:
    """yfinance 에러를 적절한 HTTP 예외로 변환"""
    error_str = str(error).lower()
    
    if "no data" in error_str or "empty" in error_str:
        return DataNotFoundError(symbol, start_date, end_date)
    elif "delisted" in error_str or "invalid" in error_str:
        return InvalidSymbolError(symbol)
    elif "rate limit" in error_str or "429" in error_str:
        return YFinanceRateLimitError()
    else:
        logger.error(f"알 수 없는 yfinance 에러: {error}")
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"데이터 수집 중 예상치 못한 오류가 발생했습니다: {error}"
        )
