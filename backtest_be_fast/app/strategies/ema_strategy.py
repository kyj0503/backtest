"""
지수 이동평균(EMA) 교차 전략 (EMA Crossover Strategy)

**역할**:
- EMA(지수 이동평균) 교차를 사용한 추세 추종 전략
- 최근 가격에 더 높은 가중치를 부여하는 이동평균

**전략 로직**:
1. 단기 EMA > 장기 EMA: 골든 크로스 → 매수
2. 단기 EMA < 장기 EMA: 데드 크로스 → 매도

**파라미터**:
- short_window: 단기 EMA 기간 (기본값: 12일)
- long_window: 장기 EMA 기간 (기본값: 26일)

**EMA vs SMA**:
- EMA: 최근 데이터에 가중치 → 빠른 반응
- SMA: 모든 데이터 동일 가중치 → 느린 반응

**사용 사례**:
- 빠른 추세 전환 포착
- 단기 매매에 적합

**의존성**:
- pandas: EMA 계산
"""
import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover


class EMAStrategy(Strategy):
    """EMA 교차 전략"""

    fast_window = 12
    slow_window = 26

    def init(self):
        close = self.data.Close
        self.ema_fast = self.I(self._ema, close, self.fast_window)
        self.ema_slow = self.I(self._ema, close, self.slow_window)

    def next(self):
        if crossover(self.ema_fast, self.ema_slow) and not self.position:
            self.buy()
        elif crossover(self.ema_slow, self.ema_fast) and self.position:
            self.position.close()

    @staticmethod
    def _ema(values, period: int):
        series = pd.Series(values)
        return series.ewm(span=period, adjust=False).mean()
