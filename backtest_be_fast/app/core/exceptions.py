"""커스텀 예외 클래스

애플리케이션의 커스텀 예외 클래스를 정의하고 HTTP 상태 코드와 매핑합니다.
"""
from fastapi import HTTPException, status
from typing import Optional
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
    def __init__(self, detail_or_symbol: str = "", start_date: str = "", end_date: str = ""):
        if start_date and end_date:
            detail = f"'{detail_or_symbol}' 종목의 데이터를 찾을 수 없습니다. (기간: {start_date} ~ {end_date})"
        else:
            detail = detail_or_symbol
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )
        logger.warning(f"데이터 없음: {detail}")


class InvalidSymbolError(HTTPException):
    """잘못된 종목 심볼일 때 발생하는 예외"""
    def __init__(self, symbol: str):
        detail = symbol if len(symbol) > 30 else f"'{symbol}'은(는) 유효하지 않은 종목 심볼입니다."
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
        logger.warning(f"잘못된 심볼: {symbol}")


class YfinanceRateLimitError(HTTPException):
    """Yahoo Finance API 제한에 도달했을 때 발생하는 예외"""
    def __init__(self, detail_or_retry: str | int = 60):
        if isinstance(detail_or_retry, int):
            detail = f"Yahoo Finance API 요청 제한에 도달했습니다. {detail_or_retry}초 후 다시 시도해주세요."
            headers = {"Retry-After": str(detail_or_retry)}
        else:
            detail = detail_or_retry
            headers = {"Retry-After": "60"}
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )
        logger.warning(f"Yahoo Finance API 제한: {detail}")


class ValidationError(HTTPException):
    """검증 실패 시 발생하는 예외"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
        logger.warning(f"검증 실패: {message}")
