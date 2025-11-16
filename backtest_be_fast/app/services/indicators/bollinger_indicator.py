"""
Bollinger Bands 기술 지표

**역할**:
- 볼린저 밴드 계산 (중간선, 상단선, 하단선)
- 가격 변동성 측정 및 추세 변화 감지
- 매수/매도 신호 포착

**특징**:
- 가격이 밴드 내에서 움직이는 특성 (약 95% 확률)
- 밴드 폭 확대: 변동성 증가
- 밴드 폭 축소: 변동성 감소
- 가격이 상단선 접근: 과매수 신호
- 가격이 하단선 접근: 과매도 신호

**파라미터**:
- period: 이동평균 기간 (기본: 20일)
- std_dev: 표준편차 배수 (기본: 2.0)

**의존성**:
- pandas: 데이터 처리
- base.py: Strategy 인터페이스
"""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from app.services.indicators.base import IndicatorStrategy

logger = logging.getLogger(__name__)


class BollingerIndicator(IndicatorStrategy):
    """Bollinger Bands 지표 계산"""

    # 기본 파라미터
    DEFAULT_PERIOD = 20
    DEFAULT_STD_DEV = 2.0

    def __init__(self):
        """Bollinger Bands 지표 초기화"""
        self.period = self.DEFAULT_PERIOD
        self.std_dev = self.DEFAULT_STD_DEV

    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Bollinger Bands를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터
            params: {
                'period': int (20),
                'std_dev': float (2.0)
            }

        Returns:
            BB_MIDDLE, BB_UPPER, BB_LOWER 컬럼이 추가된 DataFrame
        """
        # 데이터 유효성 검증
        self._validate_data(data)

        # 파라미터 설정
        if params:
            self.period = int(params.get('period', self.DEFAULT_PERIOD))
            self.std_dev = float(params.get('std_dev', self.DEFAULT_STD_DEV))

        # 유효성 검증
        if self.period <= 0:
            raise ValueError("Period must be a positive integer")

        if self.std_dev <= 0:
            raise ValueError("Standard deviation must be positive")

        if self.period > len(data):
            raise ValueError(f"Period {self.period} exceeds data length {len(data)}")

        # Bollinger Bands 계산
        result = data.copy()

        # 중간선 (SMA)
        sma = data['Close'].rolling(window=self.period).mean()

        # 표준편차
        std = data['Close'].rolling(window=self.period).std()

        # 상단선 (Upper Band) = SMA + (std_dev * std)
        upper = sma + (self.std_dev * std)

        # 하단선 (Lower Band) = SMA - (std_dev * std)
        lower = sma - (self.std_dev * std)

        # 결과에 추가
        result['BB_MIDDLE'] = sma
        result['BB_UPPER'] = upper
        result['BB_LOWER'] = lower

        # 로깅
        self._log_calculation(self.get_indicator_name(), len(result))

        return result

    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        return 'Bollinger Bands'

    def get_parameters(self) -> Dict[str, Any]:
        """기본 파라미터 반환"""
        return {
            'period': self.DEFAULT_PERIOD,
            'std_dev': self.DEFAULT_STD_DEV
        }
