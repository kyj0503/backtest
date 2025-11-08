"""
분할 매수(DCA) 계산 서비스

**역할**:
- 분할 매수(Dollar Cost Averaging) 투자의 공유 수량 및 수익률 계산
- DCA 매수 로그 생성
- 평균 단가 계산

**주요 기능**:
1. calculate_dca_shares_and_return(): DCA 투자 결과 계산
   - 총 주식 수량
   - 평균 구매 단가
   - 수익률
   - 매수 로그

**DCA(분할 매수) 개념**:
- Dollar Cost Averaging
- 일정 금액을 정기적으로 나누어 투자
- 시장 변동성 위험 분산
- 심리적 부담 감소

**사용 예**:
```python
from app.services.dca_calculator import DCACalculator

total_shares, avg_price, return_pct, log = DCACalculator.calculate_dca_shares_and_return(
    df=price_df,
    period_amount=1000.0,     # 월 1000달러
    dca_periods=12,           # 12개월
    start_date='2023-01-01',
    interval_weeks=4          # 4주마다
)
```

**의존성**:
- pandas: 데이터 처리
- datetime: 날짜 계산

**연관 컴포넌트**:
- Backend: app/services/portfolio_service.py (포트폴리오 통합)
- Backend: app/schemas/schemas.py (DCA 설정 데이터)
"""
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DCACalculator:
    """분할 매수(DCA) 계산 유틸리티"""

    @staticmethod
    def calculate_dca_shares_and_return(
        df: pd.DataFrame,
        period_amount: float,
        dca_periods: int,
        start_date: str,
        interval_weeks: int = 4
    ) -> Tuple[float, float, float, List[Dict]]:
        """
        DCA 투자의 총 주식 수량과 평균 단가, 수익률, 매수 로그를 계산 (주 단위)

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
        interval_weeks : int, optional
            투자 간격 (주 단위, 기본값: 4)

        Returns
        -------
        tuple
            (총 주식 수량, 평균 단가, 수익률 %, 매수 로그 리스트)

        Examples
        --------
        >>> total_shares, avg_price, return_pct, log = DCACalculator.calculate_dca_shares_and_return(
        ...     df=df,
        ...     period_amount=1000.0,
        ...     dca_periods=12,
        ...     start_date='2023-01-01',
        ...     interval_weeks=4
        ... )
        >>> print(f"Total shares: {total_shares}, Average price: {avg_price}")
        """
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        total_shares = 0
        total_invested = 0
        trade_log = []  # DCA 매수 기록

        for period in range(dca_periods):
            # 주 단위 계산: 시작일 + (period × interval_weeks × 7일)
            days_to_add = period * interval_weeks * 7
            investment_date = start_date_obj + timedelta(days=days_to_add)
            period_price_data = df[df.index.date >= investment_date.date()]

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
