"""
포트폴리오 리밸런싱 헬퍼 (Portfolio Rebalance Helper)

**역할**:
- 포트폴리오 리밸런싱 스케줄 판단
- 목표 비중 계산
- 리밸런싱 시점 결정

**주요 기능**:
1. is_rebalance_date(): 리밸런싱 실행 여부 판단
   - 주기별 리밸런싱 날짜 계산
   - 리밸런싱 빈도 확인

2. calculate_target_weights(): 목표 비중 계산
   - 각 자산의 목표 비중 계산
   - 현금 포함

**리밸런싱(Rebalancing) 개념**:
- 포트폴리오의 원래 비중 복원
- 정기적으로 수행 (주/월/분기 단위)
- 위험 관리 목적

**지원 리밸런싱 주기**:
- weekly_1: 매주
- weekly_2: 2주마다
- weekly_4: 4주마다 (월간)
- weekly_8: 8주마다
- weekly_12: 12주마다
- weekly_24: 24주마다
- weekly_48: 48주마다
- none: 리밸런싱 없음

**사용 예**:
```python
from app.services.rebalance_helper import RebalanceHelper

# 리밸런싱 날짜 확인
is_rebalance = RebalanceHelper.is_rebalance_date(
    current_date=datetime(2023, 2, 1),
    prev_date=datetime(2023, 1, 1),
    frequency='weekly_4',
    start_date=datetime(2023, 1, 1)
)

# 목표 비중 계산
weights = RebalanceHelper.calculate_target_weights(
    amounts={'AAPL': 5000, 'GOOGL': 5000, 'CASH': 0},
    dca_info={}
)
```

**의존성**:
- datetime: 날짜 계산
- app.schemas.schemas: 리밸런싱 주기 매핑

**연관 컴포넌트**:
- Backend: app/services/portfolio_service.py (포트폴리오 백테스트)
- Backend: app/schemas/schemas.py (DCA_FREQUENCY_MAP)
"""
from typing import Dict
from datetime import datetime
import logging
from app.schemas.schemas import DCA_FREQUENCY_MAP

logger = logging.getLogger(__name__)


class RebalanceHelper:
    """리밸런싱 유틸리티"""

    @staticmethod
    def is_rebalance_date(
        current_date: datetime,
        prev_date: datetime,
        frequency: str,
        start_date: datetime = None,
        last_rebalance_date: datetime = None
    ) -> bool:
        """
        현재 날짜가 리밸런싱 날짜인지 확인 (주 단위)

        Parameters
        ----------
        current_date : datetime
            현재 날짜
        prev_date : datetime
            이전 날짜
        frequency : str
            리밸런싱 주기 (weekly_1, weekly_2, weekly_4, weekly_8, weekly_12, weekly_24, weekly_48, none)
        start_date : datetime, optional
            시작 날짜 (폴백용)
        last_rebalance_date : datetime, optional
            마지막 리밸런싱 날짜 (우선 사용)

        Returns
        -------
        bool
            리밸런싱 실행 여부

        Examples
        --------
        >>> is_rebalance = RebalanceHelper.is_rebalance_date(
        ...     current_date=datetime(2023, 2, 1),
        ...     prev_date=datetime(2023, 1, 1),
        ...     frequency='weekly_4',
        ...     start_date=datetime(2023, 1, 1)
        ... )
        >>> print(is_rebalance)
        True
        """
        if frequency == 'none':
            return False

        # 첫 날은 리밸런싱하지 않음 (초기 매수이므로)
        if prev_date is None:
            return False

        # 주 단위 리밸런싱
        interval_weeks = DCA_FREQUENCY_MAP.get(frequency)

        if interval_weeks is None:
            # 알 수 없는 주기면 리밸런싱 안 함
            logger.warning(f"알 수 없는 리밸런싱 주기: {frequency}")
            return False

        # interval_weeks 주(7일 * interval_weeks) 이상 경과했는지 확인
        required_days = interval_weeks * 7

        # 첫 리밸런싱: last_rebalance_date가 없으면 start_date 기준으로 체크
        if last_rebalance_date is None:
            # start_date와 current_date가 같으면 첫날이므로 리밸런싱하지 않음
            if start_date and current_date == start_date:
                return False
            # Period 기반 로직: 새로운 기간에 진입했을 때만 True
            if start_date:
                current_period = ((current_date - start_date).days) // required_days
                prev_period = ((prev_date - start_date).days) // required_days
                return current_period > prev_period
            else:
                # start_date가 없으면 prev_date 기준
                current_period = ((current_date - prev_date).days) // required_days
                return current_period > 0
        else:
            # 이후 리밸런싱: 마지막 리밸런싱 날짜 기준, period 기반
            current_period = ((current_date - last_rebalance_date).days) // required_days
            prev_period = ((prev_date - last_rebalance_date).days) // required_days
            return current_period > prev_period

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
