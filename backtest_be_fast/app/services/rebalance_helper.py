"""포트폴리오 리밸런싱 헬퍼

리밸런싱 스케줄 판단 및 목표 비중 계산을 담당합니다.
Nth Weekday 방식으로 주기별 리밸런싱 날짜를 계산합니다.
"""
from typing import Dict
from datetime import datetime, timedelta
import calendar
import logging
from app.schemas.schemas import FREQUENCY_MAP

logger = logging.getLogger(__name__)


def get_weekday_occurrence(date: datetime) -> int:
    """
    날짜가 해당 월의 몇 번째 요일인지 정확히 계산
    
    Parameters
    ----------
    date : datetime
        확인할 날짜
    
    Returns
    -------
    int
        1-5: 몇 번째 해당 요일인지
        
    Examples
    --------
    >>> date = datetime(2024, 1, 26)  # 1월 26일 금요일
    >>> get_weekday_occurrence(date)
    4  # 1월의 4번째 금요일
    """
    weekday = date.weekday()
    year, month = date.year, date.month
    
    occurrence = 0
    for day in range(1, date.day + 1):
        if datetime(year, month, day).weekday() == weekday:
            occurrence += 1
    
    return occurrence


def get_nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> int:
    """
    월의 N번째 특정 요일 날짜 계산
    
    Parameters
    ----------
    year : int
        연도
    month : int
        월 (1-12)
    weekday : int
        요일 (0=월요일, 6=일요일)
    n : int
        몇 번째 주인지 (1-5)
    
    Returns
    -------
    int
        해당 월의 N번째 요일 날짜 (day)
        
    Examples
    --------
    >>> get_nth_weekday_of_month(2024, 1, 2, 2)  # 2024년 1월 2번째 수요일
    10
    """
    # 해당 월의 첫날
    first_day = datetime(year, month, 1)
    first_weekday = first_day.weekday()
    
    # 첫 번째 해당 요일까지의 일수
    days_until_target = (weekday - first_weekday) % 7
    
    # N번째 해당 요일
    target_day = 1 + days_until_target + (n - 1) * 7
    
    # 월의 마지막 날 확인
    last_day = calendar.monthrange(year, month)[1]
    
    # N번째 요일이 월을 벗어나면 마지막 해당 요일 반환
    if target_day > last_day:
        # 마지막 해당 요일 찾기
        target_day = last_day
        while datetime(year, month, target_day).weekday() != weekday:
            target_day -= 1
    
    return target_day


def get_next_nth_weekday(
    current_date: datetime,
    period_type: str,
    interval: int,
    original_nth: int = None
) -> datetime:
    """
    다음 Nth Weekday 날짜 계산 (원본 N 값 유지)

    Parameters
    ----------
    current_date : datetime
        기준 날짜
    period_type : str
        주기 타입 ('weekly', 'monthly')
    interval : int
        간격 (주 단위 또는 월 단위)
    original_nth : int, optional
        원본 "몇 번째 요일" 값 (1-5)
        None이면 current_date에서 자동 계산

    Returns
    -------
    datetime
        다음 Nth Weekday 날짜

    Examples
    --------
    >>> current = datetime(2024, 1, 31)  # 2024년 1월 5번째 수요일
    >>> # 원본 N=5를 유지하면서 다음 달 계산
    >>> next_date = get_next_nth_weekday(current, 'monthly', 1, original_nth=5)
    >>> # 2월에 5번째 수요일이 없으면 마지막 수요일 반환

    Notes
    -----
    - original_nth를 지정하면 해당 값을 계속 사용
    - 해당 월에 N번째 요일이 없으면 마지막 해당 요일로 폴백
    - 다음 달에 다시 존재하면 원래 N으로 복귀
    """
    if period_type == 'weekly':
        # 주 단위는 단순히 7일 * interval
        return current_date + timedelta(weeks=interval)
    
    elif period_type == 'monthly':
        # 현재 날짜의 "몇 번째 무슨 요일"인지 계산
        weekday = current_date.weekday()  # 0=월요일, 6=일요일
        
        # original_nth가 지정되지 않았으면 현재 날짜에서 계산
        if original_nth is None:
            original_nth = get_weekday_occurrence(current_date)
        
        # interval개월 후 계산
        target_year = current_date.year
        target_month = current_date.month + interval
        
        # 월이 12를 넘으면 연도 증가
        while target_month > 12:
            target_month -= 12
            target_year += 1
        
        # 원본 N번째 요일 계산 (없으면 자동으로 마지막 해당 요일로 폴백)
        target_day = get_nth_weekday_of_month(target_year, target_month, weekday, original_nth)
        
        return datetime(target_year, target_month, target_day)
    
    return current_date


class RebalanceHelper:
    """리밸런싱 유틸리티"""

    @staticmethod
    def is_rebalance_date(
        current_date: datetime,
        prev_date: datetime,
        frequency: str,
        start_date: datetime = None,
        last_rebalance_date: datetime = None,
        original_nth: int = None
    ) -> bool:
        """
        현재 날짜가 리밸런싱 날짜인지 확인 (Nth Weekday 방식)

        Parameters
        ----------
        current_date : datetime
            현재 날짜
        prev_date : datetime
            이전 날짜
        frequency : str
            리밸런싱 주기 (weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12, none)
        start_date : datetime, optional
            시작 날짜
        last_rebalance_date : datetime, optional
            마지막 리밸런싱 날짜
        original_nth : int, optional
            원본 "몇 번째 요일" 값 (1-5)

        Returns
        -------
        bool
            리밸런싱 실행 여부

        Examples
        --------
        >>> is_rebalance = RebalanceHelper.is_rebalance_date(
        ...     current_date=datetime(2024, 2, 14),  # 2월 2번째 수요일
        ...     prev_date=datetime(2024, 2, 13),
        ...     frequency='monthly_1',
        ...     start_date=datetime(2024, 1, 10),    # 1월 2번째 수요일
        ...     last_rebalance_date=datetime(2024, 1, 10)
        ... )
        >>> print(is_rebalance)
        True
        """
        if frequency == 'none':
            return False

        # 첫 날은 리밸런싱하지 않음 (초기 매수이므로)
        if prev_date is None or (start_date and current_date == start_date):
            return False

        # 주기 정보 가져오기
        period_info = FREQUENCY_MAP.get(frequency)
        if period_info is None:
            logger.warning(f"알 수 없는 리밸런싱 주기: {frequency}")
            return False

        period_type, interval = period_info

        # 기준 날짜 설정 (마지막 리밸런싱 날짜 또는 시작 날짜)
        reference_date = last_rebalance_date if last_rebalance_date else start_date
        
        if reference_date is None:
            return False

        # 다음 리밸런싱 날짜 계산 (Nth Weekday 방식, original_nth 유지)
        next_rebalance_date = get_next_nth_weekday(reference_date, period_type, interval, original_nth)

        # current_date가 next_rebalance_date에 도달했고, prev_date는 아직 도달하지 않았으면 True
        return current_date >= next_rebalance_date and prev_date < next_rebalance_date

    @staticmethod
    def calculate_target_weights(
        amounts: Dict[str, float],
        dca_info: Dict = None
    ) -> Dict[str, float]:
        """
        목표 비중 계산 (현금 포함)

        Parameters
        ----------
        amounts : dict
            각 종목의 투자 금액
        dca_info : dict, optional
            DCA 정보 (현재는 사용하지 않음)

        Returns
        -------
        dict
            각 종목의 목표 비중 (합이 1.0)

        Examples
        --------
        >>> weights = RebalanceHelper.calculate_target_weights(
        ...     amounts={'AAPL': 5000, 'GOOGL': 5000, 'CASH': 0}
        ... )
        >>> print(weights)
        {'AAPL': 0.5, 'GOOGL': 0.5, 'CASH': 0.0}
        """
        # 전체 투자금 계산 (현금 포함)
        total_amount = sum(amounts.values())

        if total_amount == 0:
            return {}

        # 목표 비중 계산 (현금 포함)
        target_weights = {
            k: v / total_amount
            for k, v in amounts.items()
        }

        return target_weights
