"""
MACD (Moving Average Convergence Divergence) 기술 지표

**역할**:
- MACD 지표 및 신호선 계산
- 추세 전환점 감지 및 모멘텀 판단
- 매수/매도 신호 포착

**특징**:
- MACD: 빠른 EMA - 느린 EMA
- 신호선: MACD의 EMA
- MACD가 신호선 위로: 상승 신호
- MACD가 신호선 아래로: 하락 신호
- 0선 위/아래: 추세 방향 판단

**파라미터**:
- fast_period: 빠른 EMA 기간 (기본: 12)
- slow_period: 느린 EMA 기간 (기본: 26)
- signal_period: 신호선 EMA 기간 (기본: 9)

**의존성**:
- pandas: 데이터 처리
- base.py: Strategy 인터페이스
"""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from app.services.indicators.base import IndicatorStrategy

logger = logging.getLogger(__name__)


class MacdIndicator(IndicatorStrategy):
    """MACD (Moving Average Convergence Divergence) 지표 계산"""

    # 기본 파라미터
    DEFAULT_FAST_PERIOD = 12
    DEFAULT_SLOW_PERIOD = 26
    DEFAULT_SIGNAL_PERIOD = 9

    def __init__(self):
        """MACD 지표 초기화"""
        self.fast_period = self.DEFAULT_FAST_PERIOD
        self.slow_period = self.DEFAULT_SLOW_PERIOD
        self.signal_period = self.DEFAULT_SIGNAL_PERIOD

    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        MACD를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터
            params: {
                'fast_period': int (12),
                'slow_period': int (26),
                'signal_period': int (9)
            }

        Returns:
            MACD, MACD_SIGNAL, MACD_HISTOGRAM 컬럼이 추가된 DataFrame
        """
        # 데이터 유효성 검증
        self._validate_data(data)

        # 파라미터 설정
        if params:
            self.fast_period = int(params.get('fast_period', self.DEFAULT_FAST_PERIOD))
            self.slow_period = int(params.get('slow_period', self.DEFAULT_SLOW_PERIOD))
            self.signal_period = int(params.get('signal_period', self.DEFAULT_SIGNAL_PERIOD))

        # 유효성 검증
        if self.fast_period <= 0 or self.slow_period <= 0 or self.signal_period <= 0:
            raise ValueError("All periods must be positive integers")

        if self.fast_period >= self.slow_period:
            raise ValueError("Fast period must be less than slow period")

        if self.slow_period > len(data):
            raise ValueError(f"Slow period {self.slow_period} exceeds data length {len(data)}")

        # MACD 계산
        result = data.copy()

        close = pd.Series(data['Close'])

        # 빠른 EMA (12일)
        ema_fast = close.ewm(span=self.fast_period, adjust=False).mean()

        # 느린 EMA (26일)
        ema_slow = close.ewm(span=self.slow_period, adjust=False).mean()

        # MACD = 빠른 EMA - 느린 EMA
        macd = ema_fast - ema_slow

        # 신호선 = MACD의 EMA
        signal = macd.ewm(span=self.signal_period, adjust=False).mean()

        # 히스토그램 = MACD - 신호선
        histogram = macd - signal

        # 결과에 추가
        result['MACD'] = macd
        result['MACD_SIGNAL'] = signal
        result['MACD_HISTOGRAM'] = histogram

        # 로깅
        self._log_calculation(self.get_indicator_name(), len(result))

        return result

    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        return 'MACD'

    def get_parameters(self) -> Dict[str, Any]:
        """기본 파라미터 반환"""
        return {
            'fast_period': self.DEFAULT_FAST_PERIOD,
            'slow_period': self.DEFAULT_SLOW_PERIOD,
            'signal_period': self.DEFAULT_SIGNAL_PERIOD
        }
