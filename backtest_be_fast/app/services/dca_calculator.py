"""분할 매수(DCA) 계산 서비스

Dollar Cost Averaging 투자의 총 주식 수량, 평균 단가, 수익률을 계산합니다.
"""
from typing import Dict, List, Tuple
from datetime import datetime
import pandas as pd
import logging
from app.schemas.schemas import FREQUENCY_MAP
from app.services.rebalance_helper import get_next_nth_weekday

logger = logging.getLogger(__name__)


class DcaCalculator:
    """분할 매수(DCA) 계산 유틸리티"""

    @staticmethod
    def calculate_dca_shares_and_return(
        df: pd.DataFrame,
        period_amount: float,
        dca_periods: int,
        start_date: str,
        frequency: str = 'monthly_1'
    ) -> Tuple[float, float, float, List[Dict]]:
        """
        DCA 투자의 총 주식 수량과 평균 단가, 수익률, 매수 로그를 계산 (Nth Weekday 방식)

        Parameters
        ----------
        df : pd.DataFrame
            가격 데이터 (Close 컬럼 필수)
        period_amount : float
            회당 투자 금액
        dca_periods : int
            총 투자 횟수
        start_date : str
            시작 날짜 (YYYY-MM-DD 형식)
        frequency : str, optional
            투자 주기 (weekly_1, weekly_2, monthly_1, monthly_2, monthly_3, monthly_6, monthly_12, 기본값: monthly_1)

        Returns
        -------
        tuple
            (총 주식 수량, 평균 단가, 수익률 %, 매수 로그 리스트)

        Examples
        --------
        >>> total_shares, avg_price, return_pct, log = DcaCalculator.calculate_dca_shares_and_return(
        ...     df=df,
        ...     period_amount=1000.0,
        ...     dca_periods=12,
        ...     start_date='2024-01-10',
        ...     frequency='monthly_1'
        ... )
        >>> print(f"Total shares: {total_shares}, Average price: {avg_price}")
        """
        # 주기 정보 가져오기
        period_info = FREQUENCY_MAP.get(frequency)
        if not period_info:
            logger.warning(f"알 수 없는 DCA 주기: {frequency}, 기본값 monthly_1 사용")
            period_info = FREQUENCY_MAP['monthly_1']
        
        period_type, interval = period_info
        
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        total_shares = 0
        total_invested = 0
        trade_log = []  # DCA 매수 기록

        current_investment_date = start_date_obj

        for period in range(dca_periods):
            # Nth Weekday 방식으로 다음 투자 날짜 계산
            if period > 0:
                current_investment_date = get_next_nth_weekday(current_investment_date, period_type, interval)
            
            # 해당 날짜 이후의 첫 거래일 찾기
            period_price_data = df[df.index.date >= current_investment_date.date()]

            if not period_price_data.empty:
                period_price = period_price_data['Close'].iloc[0]
                actual_date = period_price_data.index[0]
                shares_bought = period_amount / period_price
                total_shares += shares_bought
                total_invested += period_amount

                # DCA 매수 기록 추가
                trade_log.append({
                    'EntryTime': actual_date.isoformat(),
                    'EntryPrice': float(period_price),
                    'Size': float(shares_bought),
                    'Type': 'BUY',
                    'ExitTime': None,  # DCA는 매수만 있고 매도 없음
                    'ExitPrice': None,
                    'PnL': None,
                    'ReturnPct': None,
                    'Duration': None,
                })

        if total_shares > 0:
            average_price = total_invested / total_shares
            end_price = df['Close'].iloc[-1]
            return_rate = (end_price / average_price - 1) * 100
            return total_shares, average_price, return_rate, trade_log

        return 0, 0, 0, []
