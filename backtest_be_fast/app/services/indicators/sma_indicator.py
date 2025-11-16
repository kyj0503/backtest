"""
Simple Moving Average (SMA) 기술 지표

**역할**:
- 단순 이동 평균 계산 (Simple Moving Average)
- 가격 추세 확인 및 지지/저항 수준 파악
- 단기(short_window)와 장기(long_window) SMA 계산

**특징**:
- 간단하고 직관적인 추세 지표
- 느린 응답 속도 (lag)
- 주로 다른 지표와 함께 사용

**파라미터**:
- short_window: 단기 SMA 기간 (기본: 10일)
- long_window: 장기 SMA 기간 (기본: 20일)

**의존성**:
- pandas: 데이터 처리
- base.py: Strategy 인터페이스
"""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from app.services.indicators.base import IndicatorStrategy

logger = logging.getLogger(__name__)


class SmaIndicator(IndicatorStrategy):
    """Simple Moving Average (SMA) 지표 계산"""

    # 기본 파라미터
    DEFAULT_SHORT_WINDOW = 10
    DEFAULT_LONG_WINDOW = 20

    def __init__(self):
        """SMA 지표 초기화"""
        self.short_window = self.DEFAULT_SHORT_WINDOW
        self.long_window = self.DEFAULT_LONG_WINDOW

    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        SMA를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터
            params: {'short_window': int, 'long_window': int}

        Returns:
            SMA_short와 SMA_long 컬럼이 추가된 DataFrame
        """
        # 데이터 유효성 검증
        self._validate_data(data)

        # 파라미터 설정
        if params:
            self.short_window = params.get('short_window', self.DEFAULT_SHORT_WINDOW)
            self.long_window = params.get('long_window', self.DEFAULT_LONG_WINDOW)

        # 유효성 검증
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Window sizes must be positive integers")

        if self.short_window > len(data):
            raise ValueError(f"Short window {self.short_window} exceeds data length {len(data)}")

        if self.long_window > len(data):
            raise ValueError(f"Long window {self.long_window} exceeds data length {len(data)}")

        # SMA 계산
        result = data.copy()
        result[f'SMA_{self.short_window}'] = data['Close'].rolling(
            window=self.short_window
        ).mean()
        result[f'SMA_{self.long_window}'] = data['Close'].rolling(
            window=self.long_window
        ).mean()

        # 로깅
        self._log_calculation(self.get_indicator_name(), len(result))

        return result

    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        return 'SMA'

    def get_parameters(self) -> Dict[str, Any]:
        """기본 파라미터 반환"""
        return {
            'short_window': self.DEFAULT_SHORT_WINDOW,
            'long_window': self.DEFAULT_LONG_WINDOW
        }
