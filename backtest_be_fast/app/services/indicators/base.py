"""
기술 지표 계산 전략 기본 클래스

**역할**:
- 모든 지표 구현을 위한 추상 인터페이스 정의
- Strategy Pattern 적용으로 OCP 준수
- 새로운 지표 추가 시 기존 코드 수정 불필요

**의존성**:
- pandas: 데이터 처리
- typing: 타입 힌팅

**연관 컴포넌트**:
- Backend: app/services/indicators/*.py (구체적인 지표 구현)
- Backend: app/services/chart_data_service.py (지표 사용)
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class IndicatorStrategy(ABC):
    """기술 지표 계산 전략 인터페이스"""

    @abstractmethod
    def calculate(
        self,
        data: pd.DataFrame,
        params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        지표를 계산하고 DataFrame에 추가합니다.

        Args:
            data: OHLCV 데이터 (Open, High, Low, Close, Volume)
            params: 지표별 파라미터 (예: {'sma_period': 20})

        Returns:
            지표 값이 추가된 DataFrame (원본 컬럼 + 지표 컬럼)

        Raises:
            ValueError: 데이터가 부족하거나 파라미터가 유효하지 않은 경우
        """
        pass

    @abstractmethod
    def get_indicator_name(self) -> str:
        """
        지표의 이름을 반환합니다.

        Returns:
            지표 이름 (예: 'SMA', 'RSI', 'Bollinger Bands')
        """
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """
        지표의 기본 파라미터를 반환합니다.

        Returns:
            파라미터 딕셔너리 (예: {'sma_period': 20})
        """
        pass

    def _validate_data(self, data: pd.DataFrame) -> None:
        """
        데이터의 유효성을 검증합니다.

        Args:
            data: 검증할 DataFrame

        Raises:
            ValueError: 필수 컬럼이 없거나 데이터가 비어있는 경우
        """
        if data is None or data.empty:
            raise ValueError("Data cannot be empty")

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]

        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

    def _log_calculation(self, indicator_name: str, rows: int) -> None:
        """
        지표 계산 결과를 로깅합니다.

        Args:
            indicator_name: 지표 이름
            rows: 계산된 행 수
        """
        logger.debug(f"Calculated {indicator_name} indicator: {rows} data points")
