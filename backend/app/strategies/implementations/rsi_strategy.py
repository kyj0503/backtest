"""
RSI 전략 (Relative Strength Index Strategy)
"""
import pandas as pd
import numpy as np
from backtesting import Strategy


class RSIStrategy(Strategy):
    """RSI 전략 - 개선된 버전"""
    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    position_size = 0.95  # 95% 포지션 사용
    
    def init(self):
        close = self.data.Close
        self.rsi = self.I(self._rsi, close, self.rsi_period)
    
    def _rsi(self, close: pd.Series, period: int) -> pd.Series:
        """RSI 계산 - 안정성 개선"""
        close = pd.Series(close)
        delta = close.diff()
        
        # 상승분과 하락분 분리
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 지수 이동평균으로 평균 계산 (더 안정적)
        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
        
        # 0으로 나누는 것 방지
        avg_loss = avg_loss.replace(0, np.finfo(float).eps)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.fillna(50)  # NaN 값을 50으로 채움
    
    def next(self):
        if len(self.rsi) > self.rsi_period:  # 충분한 데이터가 있을 때만 실행
            current_rsi = self.rsi[-1]
            
            # 과매도 구간에서 매수
            if current_rsi < self.rsi_oversold and not self.position:
                self.buy(size=self.position_size)
            
            # 과매수 구간에서 매도
            elif current_rsi > self.rsi_overbought and self.position:
                self.sell(size=self.position.size)
