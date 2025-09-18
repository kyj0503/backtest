"""
사용자 친화적 에러 메시지 매핑
"""
import uuid
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "NO_DATA": {
        "ko": "선택한 기간에 대한 데이터가 없습니다. 다른 기간을 선택해주세요.",
        "en": "No data available for the selected period. Please choose a different period."
    },
    "INVALID_SYMBOL": {
        "ko": "존재하지 않는 종목 심볼입니다. 올바른 심볼을 입력해주세요.",
        "en": "Invalid stock symbol. Please enter a valid symbol."
    },
    "RATE_LIMIT": {
        "ko": "잠시 후 다시 시도해주세요. (요청이 너무 많습니다)",
        "en": "Please try again later. (Too many requests)"
    },
    "DATE_RANGE_ERROR": {
        "ko": "시작 날짜는 종료 날짜보다 빨라야 합니다.",
        "en": "Start date must be earlier than end date."
    },
    "PORTFOLIO_EMPTY": {
        "ko": "포트폴리오에 최소 1개 종목을 추가해주세요.",
        "en": "Please add at least one stock to your portfolio."
    },
    "AMOUNT_INVALID": {
        "ko": "투자 금액은 0보다 커야 합니다.",
        "en": "Investment amount must be greater than 0."
    },
    "DataNotFoundError": {
        "ko": "데이터를 찾을 수 없습니다. 종목 심볼이나 날짜 범위를 확인해주세요.",
        "en": "Data not found. Please check the symbol or date range."
    },
    "InvalidSymbolError": {
        "ko": "유효하지 않은 종목 심볼입니다.",
        "en": "Invalid stock symbol."
    },
    "YFinanceRateLimitError": {
        "ko": "데이터 제공업체 요청 제한에 도달했습니다. 잠시 후 다시 시도해주세요.",
        "en": "Data provider rate limit reached. Please try again later."
    },
    "ValidationError": {
        "ko": "입력값이 올바르지 않습니다.",
        "en": "Invalid input values."
    },
    "portfolio_backtest_error": {
        "ko": "포트폴리오 백테스트 실행 중 오류가 발생했습니다.",
        "en": "Error occurred during portfolio backtest execution."
    },
    "unexpected_error": {
        "ko": "예상치 못한 오류가 발생했습니다. 문제가 지속되면 관리자에게 문의하세요.",
        "en": "An unexpected error occurred. Please contact administrator if the problem persists."
    }
}

def get_user_friendly_message(error_code: str, original_message: str = "", language: str = "ko") -> str:
    """사용자 친화적 에러 메시지 반환"""
    if error_code in ERROR_MESSAGES:
        friendly_msg = ERROR_MESSAGES[error_code].get(language, ERROR_MESSAGES[error_code]["ko"])
        # 원본 메시지가 있고 유용한 정보를 포함하고 있으면 추가
        if original_message and len(original_message) < 200:
            return f"{friendly_msg} (상세: {original_message})"
        return friendly_msg
    return f"알 수 없는 오류가 발생했습니다. ({original_message[:100]}...)" if original_message else "알 수 없는 오류가 발생했습니다."

def log_error_for_debugging(error: Exception, operation: str, context: Dict[str, Any] = None) -> str:
    """디버깅을 위한 에러 로깅 및 고유 ID 반환"""
    error_id = str(uuid.uuid4())[:8]
    context_str = f", 컨텍스트: {context}" if context else ""
    
    logger.error(f"[오류 ID: {error_id}] {operation} 실패: {str(error)}{context_str}")
    
    return error_id

# 백테스트 결과 해석 도우미
BACKTEST_TIPS = {
    "high_return": "🎉 훌륭한 수익률입니다! 하지만 과거 성과가 미래를 보장하지는 않습니다.",
    "high_volatility": "⚠️ 변동성이 높습니다. 리스크 관리를 고려해보세요.",
    "low_sharpe": "📊 샤프 비율이 낮습니다. 위험 대비 수익이 좋지 않을 수 있습니다.",
    "high_drawdown": "📉 최대 낙폭이 큽니다. 심리적 부담을 고려해보세요."
}
