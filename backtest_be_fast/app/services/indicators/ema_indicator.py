"""
EMA (Exponential Moving Average) 기술 지표

**역할**:
- 지수이동평균 (Exponential Moving Average) 계산
- SMA보다 빠른 반응 속도
- 최근 데이터에 더 큰 가중치 부여

**특징**:
- SMA보다 최근 가격 변화에 민감
- 추세 전환을 더 빨리 감지
- 단기 기술 분석에 자주 사용
- 다른 지표의 구성 요소로도 사용 (MACD, RSI 등)

**파라미터**:
- short_span: 단기 EMA 기간 (기본: 12)
- long_span: 장기 EMA 기간 (기본: 26)

**의존성**:
- pandas: 데이터 처리
- base.py: Strategy 인터페이스
"""

from typing import Dict, Any, Optional
import pandas as pd
import logging

from app.services.indicators.base import IndicatorStrategy

logger = logging.getLogger(__name__)


class EmaIndicator(IndicatorStrategy):
    """EMA (Exponential Moving Average) 지표 계산"""

    # 기본 파라미터
    DEFAULT_SHORT_SPAN = 12
    DEFAULT_LONG_SPAN = 26

    def __init__(self):
        """EMA 지표 초기화"""
        self.short_span = self.DEFAULT_SHORT_SPAN
        self.long_span = self.DEFAULT_LONG_SPAN

    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        EMA를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터
            params: {
                'short_span': int (12),
                'long_span': int (26)
            }

        Returns:
            EMA_short와 EMA_long 컬럼이 추가된 DataFrame
        """
        # 데이터 유효성 검증
        self._validate_data(data)

        # 파라미터 설정
        if params:
            self.short_span = int(params.get('short_span', self.DEFAULT_SHORT_SPAN))
            self.long_span = int(params.get('long_span', self.DEFAULT_LONG_SPAN))

        # 유효성 검증
        if self.short_span <= 0 or self.long_span <= 0:
            raise ValueError("Span values must be positive integers")

        if self.short_span >= self.long_span:
            raise ValueError("Short span must be less than long span")

        if self.long_span > len(data):
            raise ValueError(f"Long span {self.long_span} exceeds data length {len(data)}")

        # EMA 계산
        result = data.copy()

        # 단기 EMA (12일)
        result[f'EMA_{self.short_span}'] = data['Close'].ewm(
            span=self.short_span,
            adjust=False
        ).mean()

        # 장기 EMA (26일)
        result[f'EMA_{self.long_span}'] = data['Close'].ewm(
            span=self.long_span,
            adjust=False
        ).mean()

        # 로깅
        self._log_calculation(self.get_indicator_name(), len(result))

        return result

    def get_indicator_name(self) -> str:
        """지표 이름 반환"""
        return 'EMA'

    def get_parameters(self) -> Dict[str, Any]:
        """기본 파라미터 반환"""
        return {
            'short_span': self.DEFAULT_SHORT_SPAN,
            'long_span': self.DEFAULT_LONG_SPAN
        }
