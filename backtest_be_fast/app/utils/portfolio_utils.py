"""
포트폴리오 백테스트 유틸리티 함수들
"""
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class PortfolioValidationError(Exception):
    """포트폴리오 검증 오류"""
    pass

class DataLoadError(Exception):
    """데이터 로드 오류"""
    pass

def validate_portfolio_request(portfolio: List, start_date: str, end_date: str) -> None:
    """포트폴리오 요청 검증"""
    if not portfolio:
        raise PortfolioValidationError("포트폴리오는 최소 1개 종목을 포함해야 합니다.")
    
    if len(portfolio) > 10:
        raise PortfolioValidationError("포트폴리오는 최대 10개 종목까지 포함할 수 있습니다.")
    
    # 날짜 검증
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if end <= start:
            raise PortfolioValidationError("종료 날짜는 시작 날짜보다 이후여야 합니다.")
    except ValueError as e:
        raise PortfolioValidationError(f"날짜 형식 오류: {e}")

def generate_unique_key(symbol: str, idx: int) -> str:
    """중복 종목을 위한 고유 키 생성"""
    return f"{symbol}_{idx}"

def parse_unique_key(unique_key: str) -> Tuple[str, int]:
    """고유 키에서 심볼과 인덱스 파싱"""
    parts = unique_key.rsplit('_', 1)
    if len(parts) == 2:
        try:
            return parts[0], int(parts[1])
        except ValueError:
            pass
    return unique_key, 0

def calculate_portfolio_weights(amounts: Dict[str, float]) -> Dict[str, float]:
    """포트폴리오 가중치 계산"""
    total_amount = sum(amounts.values())
    if total_amount <= 0:
        raise PortfolioValidationError("총 투자 금액은 0보다 커야 합니다.")
    
    return {key: amount / total_amount for key, amount in amounts.items()}

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """안전한 나눗셈 (0으로 나누기 방지)"""
    if denominator == 0:
        return default
    return numerator / denominator

def format_currency(amount: float) -> str:
    """통화 형식 포맷팅"""
    return f"${amount:,.2f}"

def log_portfolio_info(portfolio_items: List, logger_instance: logging.Logger) -> None:
    """포트폴리오 정보 로깅"""
    total_amount = sum(item.amount for item in portfolio_items)
    logger_instance.info(f"포트폴리오 백테스트 시작: 총 {len(portfolio_items)}개 항목, 총 투자금액: {format_currency(total_amount)}")
    
    for idx, item in enumerate(portfolio_items):
        investment_type = getattr(item, 'investment_type', 'lump_sum')
        if investment_type == 'dca':
            dca_periods = getattr(item, 'dca_periods', 12)
            monthly_amount = item.amount / dca_periods
            logger_instance.info(
                f"  #{idx+1}: {item.symbol} - {format_currency(item.amount)} "
                f"(DCA: {dca_periods}개월, 월 {format_currency(monthly_amount)})"
            )
        else:
            logger_instance.info(f"  #{idx+1}: {item.symbol} - {format_currency(item.amount)} (일시불)")
