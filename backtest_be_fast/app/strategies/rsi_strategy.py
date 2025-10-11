"""
RSI 전략 (Relative Strength Index Strategy)

**역할**:
- RSI(상대강도지수) 지표를 사용한 역추세 매매 전략
- 과매도/과매수 구간에서 반대 방향 포지션 진입

**전략 로직**:
1. RSI < oversold (예: 30): 과매도 → 매수
2. RSI > overbought (예: 70): 과매수 → 매도

**파라미터**:
- rsi_period: RSI 계산 기간 (기본값: 14일)
- rsi_oversold: 과매도 기준선 (기본값: 30)
- rsi_overbought: 과매수 기준선 (기본값: 70)

**RSI 계산**:
- RSI = 100 - (100 / (1 + RS))
- RS = 평균 상승폭 / 평균 하락폭

**사용 사례**:
- 단기 과열/침체 구간 매매
- 변동성 큰 종목에 효과적

**의존성**:
- pandas, numpy: RSI 계산
- backtesting.py: Strategy 베이스 클래스
"""
import pandas as pd
import numpy as np
from backtesting import Strategy


class RSIStrategy(Strategy):
    """
    RSI 기반 매매 전략
    
    RSI(Relative Strength Index) 지표를 사용하여 과매도/과매수 구간에서 매매하는 전략
    """
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
        if len(self.rsi) > self.rsi_period:
            current_rsi = self.rsi[-1]

            if current_rsi < self.rsi_oversold and not self.position:
                price = self.data.Close[-1]
                size = int((self.equity * self.position_size) / price)
                if size > 0:
                    self.buy(size=size)

            elif current_rsi > self.rsi_overbought and self.position:
                self.position.close()


class AggressiveRSIStrategy(RSIStrategy):
    """
    보다 공격적인 RSI 전략
    더 넓은 RSI 범위와 100% 포지션 사용
    """
    rsi_oversold = 25       # 더 낮은 과매도 기준
    rsi_overbought = 75     # 더 높은 과매수 기준
    position_size = 1.0     # 100% 포지션


class ConservativeRSIStrategy(RSIStrategy):
    """
    보수적인 RSI 전략
    더 좁은 RSI 범위와 50% 포지션 사용
    """
    rsi_oversold = 35       # 더 높은 과매도 기준
    rsi_overbought = 65     # 더 낮은 과매수 기준
    position_size = 0.5     # 50% 포지션
