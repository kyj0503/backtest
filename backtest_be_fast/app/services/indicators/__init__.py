"""
지표(Indicator) Strategy 패턴 구현

**역할**:
- 모든 기술 지표 전략 및 팩토리 제공
- 플러그 앤 플레이 지표 등록 및 조회
- 새로운 지표 추가 시 기존 코드 수정 없음 (Open/Closed Principle)

**구조**:
- base.py: IndicatorStrategy 추상 기본 클래스
- sma_indicator.py: SMA 지표 구현
- rsi_indicator.py: RSI 지표 구현
- bollinger_indicator.py: Bollinger Bands 지표 구현
- macd_indicator.py: MACD 지표 구현
- ema_indicator.py: EMA 지표 구현

**사용 방법**:
1. 직접 사용:
   ```python
   from app.services.indicators import get_indicator

   sma = get_indicator('SMA')
   result = sma.calculate(data, {'short_window': 10, 'long_window': 20})
   ```

2. 팩토리를 통한 동적 사용:
   ```python
   from app.services.indicators import indicator_factory

   indicator = indicator_factory.get_indicator(strategy_name)
   result = indicator.calculate(data, params)
   ```

**지원 지표**:
- SMA (Simple Moving Average)
- RSI (Relative Strength Index)
- Bollinger Bands (볼린저 밴드)
- MACD (Moving Average Convergence Divergence)
- EMA (Exponential Moving Average)
"""

from app.services.indicators.base import IndicatorStrategy
from app.services.indicators.sma_indicator import SmaIndicator
from app.services.indicators.rsi_indicator import RsiIndicator
from app.services.indicators.bollinger_indicator import BollingerIndicator
from app.services.indicators.macd_indicator import MacdIndicator
from app.services.indicators.ema_indicator import EmaIndicator


class IndicatorFactory:
    """지표 팩토리 - 지표 인스턴스 생성 및 관리"""

    def __init__(self):
        """팩토리 초기화 및 기본 지표 등록"""
        self._indicators = {}
        self._register_default_indicators()

    def _register_default_indicators(self):
        """기본 지표 등록"""
        self.register('SMA', SmaIndicator())
        self.register('RSI', RsiIndicator())
        self.register('Bollinger Bands', BollingerIndicator())
        self.register('MACD', MacdIndicator())
        self.register('EMA', EmaIndicator())

    def register(self, name: str, indicator: IndicatorStrategy):
        """
        새로운 지표 등록 (확장성)

        Args:
            name: 지표 이름 (팩토리에서 조회할 때 사용)
            indicator: IndicatorStrategy를 구현한 인스턴스

        Raises:
            TypeError: indicator가 IndicatorStrategy를 구현하지 않은 경우
        """
        if not isinstance(indicator, IndicatorStrategy):
            raise TypeError(
                f"Indicator must implement IndicatorStrategy interface. "
                f"Got {type(indicator).__name__}"
            )
        self._indicators[name] = indicator

    def get_indicator(self, name: str) -> IndicatorStrategy:
        """
        지표 인스턴스 조회

        Args:
            name: 지표 이름

        Returns:
            IndicatorStrategy 인스턴스

        Raises:
            KeyError: 등록되지 않은 지표명
        """
        if name not in self._indicators:
            available = ', '.join(self._indicators.keys())
            raise KeyError(
                f"Indicator '{name}' not found. "
                f"Available indicators: {available}"
            )
        return self._indicators[name]

    def get_available_indicators(self) -> list:
        """
        등록된 모든 지표 이름 반환

        Returns:
            지표 이름 리스트
        """
        return list(self._indicators.keys())

    def list_indicators(self) -> dict:
        """
        등록된 모든 지표 정보 반환

        Returns:
            {지표이름: 지표정보} 딕셔너리
        """
        return {
            name: {
                'name': indicator.get_indicator_name(),
                'parameters': indicator.get_parameters()
            }
            for name, indicator in self._indicators.items()
        }


# 글로벌 팩토리 인스턴스
indicator_factory = IndicatorFactory()


def get_indicator(name: str) -> IndicatorStrategy:
    """
    팩토리를 통해 지표 인스턴스 조회 (편의 함수)

    Args:
        name: 지표 이름

    Returns:
        IndicatorStrategy 인스턴스
    """
    return indicator_factory.get_indicator(name)


__all__ = [
    'IndicatorStrategy',
    'SmaIndicator',
    'RsiIndicator',
    'BollingerIndicator',
    'MacdIndicator',
    'EmaIndicator',
    'IndicatorFactory',
    'indicator_factory',
    'get_indicator',
]
