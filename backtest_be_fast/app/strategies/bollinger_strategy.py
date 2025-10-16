"""
볼린저 밴드 전략 (Bollinger Bands Strategy)

**역할**:
- 볼린저 밴드를 사용한 변동성 기반 매매 전략
- 가격이 밴드 경계를 돌파할 때 매매

**전략 로직**:
1. 가격 < 하단 밴드: 과매도 → 매수
2. 가격 > 상단 밴드: 과매수 → 매도

**파라미터**:
- bollinger_period: 이동평균 기간 (기본값: 20일)
- bollinger_std: 표준편차 배수 (기본값: 2)

**볼린저 밴드 계산**:
- 중심선: 20일 이동평균
- 상단 밴드: 중심선 + (2 × 표준편차)
- 하단 밴드: 중심선 - (2 × 표준편차)

**사용 사례**:
- 변동성 급증 시 반전 매매
- 밴드 축소 후 돌파 시 추세 전환 포착

**의존성**:
- pandas, numpy: 볼린저 밴드 계산
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.test import SMA


class BollingerBandsStrategy(Strategy):
    """볼린저 밴드 전략"""
    period = 20
    std_dev = 2
    position_size = 0.95  # 95% 포지션 사용
    
    def init(self):
        close = self.data.Close
        self.sma = self.I(SMA, close, self.period)
        self.upper_band = self.I(self._upper_band, close, self.period, self.std_dev)
        self.lower_band = self.I(self._lower_band, close, self.period, self.std_dev)
    
    def _upper_band(self, close: pd.Series, period: int, std_dev: float) -> pd.Series:
        """상단 볼린저 밴드 계산"""
        close = pd.Series(close)
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        return sma + (std_dev * std)
    
    def _lower_band(self, close: pd.Series, period: int, std_dev: float) -> pd.Series:
        """하단 볼린저 밴드 계산"""
        close = pd.Series(close)
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        return sma - (std_dev * std)
    
    def next(self):
        if len(self.data) < self.period:
            return
        
        if (len(self.upper_band) > 0 and len(self.lower_band) > 0 and 
            not np.isnan(self.upper_band[-1]) and not np.isnan(self.lower_band[-1])):
            
            current_price = self.data.Close[-1]
            
            # 가격이 하단 밴드 아래로 떨어짐: 과매도 → 매수
            if current_price < self.lower_band[-1] and not self.position:
                price = self.data.Close[-1]
                size = int((self.equity * self.position_size) / price)
                if size > 0:
                    self.buy(size=size)
            # 가격이 상단 밴드 위로 올라감 또는 중심선(SMA) 복귀: 매도
            elif self.position:
                if current_price > self.upper_band[-1]:
                    # 과매수 구간: 매도
                    self.position.close()
                elif current_price >= self.sma[-1] and len(self.sma) > 1:
                    # 하단에서 매수했으므로 중심선 복귀 시 이익 실현
                    self.position.close()
