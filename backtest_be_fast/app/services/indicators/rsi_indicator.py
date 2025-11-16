"""
Relative Strength Index (RSI) 기술 지표

**역할**:
- 상대강도지수 (Relative Strength Index) 계산
- 과매수(overbought)와 과매도(oversold) 상태 감지
- 가격 추세의 강도와 방향 판단

**특징**:
- 0~100 사이의 값
- 70 이상: 과매수 (상승 추세 약화 신호)
- 30 이하: 과매도 (하락 추세 약화 신호)
- 모멘텀 지표

**파라미터**:
- rsi_period: RSI 계산 기간 (기본: 14일)
- rsi_overbought: 과매수 기준값 (기본: 70)
- rsi_oversold: 과매도 기준값 (기본: 30)

**의존성**:
- pandas: 데이터 처리
- numpy: 수치 계산
- base.py: Strategy 인터페이스
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
import logging

from app.services.indicators.base import IndicatorStrategy

logger = logging.getLogger(__name__)


class RsiIndicator(IndicatorStrategy):
    """Relative Strength Index (RSI) 지표 계산"""

    # 기본 파라미터
    DEFAULT_PERIOD = 14
    DEFAULT_OVERBOUGHT = 70
    DEFAULT_OVERSOLD = 30

    def __init__(self):
        """RSI 지표 초기화"""
        self.period = self.DEFAULT_PERIOD
        self.overbought = self.DEFAULT_OVERBOUGHT
        self.oversold = self.DEFAULT_OVERSOLD

    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        RSI를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터
            params: {
                'rsi_period': int (14),
                'rsi_overbought': float (70),
                'rsi_oversold': float (30)
            }

        Returns:
            RSI, RSI_OVERBOUGHT, RSI_OVERSOLD 컬럼이 추가된 DataFrame
        """
        # 데이터 유효성 검증
        self._validate_data(data)

        # 파라미터 설정
        if params:
            self.period = int(params.get('rsi_period', self.DEFAULT_PERIOD))
            self.overbought = float(params.get('rsi_overbought', self.DEFAULT_OVERBOUGHT))
            self.oversold = float(params.get('rsi_oversold', self.DEFAULT_OVERSOLD))

        # 유효성 검증
        if self.period <= 0:
            raise ValueError("Period must be a positive integer")

        if self.period > len(data):
            raise ValueError(f"Period {self.period} exceeds data length {len(data)}")

        # RSI 계산
        result = data.copy()

        # Close 가격의 변화도 계산
        close = pd.Series(data['Close'])
        delta = close.diff()

        # 상승폭과 하락폭 분리
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # EMA를 사용한 평균 (상승폭과 하락폭의 지수이동평균)
        avg_gain = gain.ewm(alpha=1 / self.period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / self.period, adjust=False).mean()

        # 0으로 나누기 방지
        avg_loss = avg_loss.replace(0, np.finfo(float).eps)

        # RS (Relative Strength) 계산
        rs = avg_gain / avg_loss

        # RSI 계산: 100 - (100 / (1 + RS))
        rsi = 100 - (100 / (1 + rs))

        # 결과에 추가
        result[f'RSI_{self.period}'] = rsi
        result[f'RSI_OVERBOUGHT'] = self.overbought
        result[f'RSI_OVERSOLD'] = self.oversold

        # 로깅
        self._log_calculation(self.get_indicator_name(), len(result))

        return result

    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        return 'RSI'

    def get_parameters(self) -> Dict[str, Any]:
        """기본 파라미터 반환"""
        return {
            'rsi_period': self.DEFAULT_PERIOD,
            'rsi_overbought': self.DEFAULT_OVERBOUGHT,
            'rsi_oversold': self.DEFAULT_OVERSOLD
        }
