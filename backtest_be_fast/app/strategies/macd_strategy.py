"""
MACD 전략 (Moving Average Convergence Divergence Strategy)

**역할**:
- MACD 지표를 사용한 추세 추종 및 모멘텀 전략
- MACD 선과 시그널 선의 교차로 매매

**전략 로직**:
1. MACD > 시그널: 상승 추세 → 매수
2. MACD < 시그널: 하락 추세 → 매도

**파라미터**:
- macd_fast: 단기 EMA 기간 (기본값: 12일)
- macd_slow: 장기 EMA 기간 (기본값: 26일)
- macd_signal: 시그널 EMA 기간 (기본값: 9일)

**MACD 계산**:
- MACD = EMA(12) - EMA(26)
- Signal = EMA(MACD, 9)
- Histogram = MACD - Signal

**사용 사례**:
- 중장기 추세 전환 포착
- 모멘텀 강도 측정

**의존성**:
- pandas, numpy: MACD 계산
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover


class MACDStrategy(Strategy):
    """MACD 전략"""
    fast_period = 12
    slow_period = 26
    signal_period = 9
    
    def init(self):
        close = self.data.Close
        self.macd_line = self.I(self._macd_line, close, self.fast_period, self.slow_period)
        self.signal_line = self.I(self._signal_line, close, self.fast_period, self.slow_period, self.signal_period)
    
    def _macd_line(self, close: pd.Series, fast: int, slow: int) -> pd.Series:
        """MACD 라인 계산"""
        close = pd.Series(close)
        exp1 = close.ewm(span=fast).mean()
        exp2 = close.ewm(span=slow).mean()
        return exp1 - exp2
    
    def _signal_line(self, close: pd.Series, fast: int, slow: int, signal: int) -> pd.Series:
        """시그널 라인 계산"""
        macd = self._macd_line(close, fast, slow)
        return macd.ewm(span=signal).mean()
    
    def next(self):
        if (len(self.macd_line) > 1 and len(self.signal_line) > 1 and
            not np.isnan(self.macd_line[-1]) and not np.isnan(self.signal_line[-1])):
            
            if crossover(self.macd_line, self.signal_line) and not self.position:
                self.buy()
            elif crossover(self.signal_line, self.macd_line) and self.position:
                self.position.close()
