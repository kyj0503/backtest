"""백테스팅 전략 모음

Buy & Hold, SMA, EMA, RSI, Bollinger Bands, MACD 등 6가지 전략을 구현합니다.
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA


# ========================
# Mixin: Position Sizing
# ========================

class PositionSizingMixin:
    """위치 조정 기능을 제공하는 Mixin (기본 포지션 크기: 0.95)"""

    position_size = 0.95

    def calculate_and_buy(self, price=None):
        """포지션 크기에 따라 매수 가능한 수량을 계산하여 매수"""
        if price is None:
            price = self.data.Close[-1]

        size = int((self.equity * self.position_size) / price)

        if size > 0:
            self.buy(size=size)


# ========================
# Strategy: Buy & Hold
# ========================

class BuyAndHoldStrategy(Strategy):
    """매수 후 보유 전략

    가장 단순한 전략: 백테스트 시작 시점에 전액 매수하고 끝까지 보유
    """

    def init(self):
        self.bought = False

    def next(self):
        if not self.bought:
            self.buy()
            self.bought = True


# ========================
# Strategy: SMA Crossover
# ========================

def _sma_helper(values, n):
    """단순 이동평균(Simple Moving Average) 계산"""
    return pd.Series(values).rolling(n).mean()


class SmaCrossStrategy(PositionSizingMixin, Strategy):
    """이동평균 교차 전략 (단기선이 장기선을 상향/하향 돌파 시 매매)"""

    sma_short = 10
    sma_long = 20
    position_size = 0.95

    def init(self):
        self.sma1 = self.I(_sma_helper, self.data.Close, self.sma_short)
        self.sma2 = self.I(_sma_helper, self.data.Close, self.sma_long)

    def next(self):
        if not self.position:
            if crossover(self.sma1, self.sma2):
                self.calculate_and_buy()
        else:
            if crossover(self.sma2, self.sma1):
                self.position.close()


# ========================
# Strategy: EMA Crossover
# ========================

class EmaStrategy(PositionSizingMixin, Strategy):
    """EMA 교차 전략 (지수 이동평균 교차로 매매)"""

    fast_window = 12
    slow_window = 26
    position_size = 0.95

    def init(self):
        close = self.data.Close
        self.ema_fast = self.I(self._ema, close, self.fast_window)
        self.ema_slow = self.I(self._ema, close, self.slow_window)

    def next(self):
        if crossover(self.ema_fast, self.ema_slow) and not self.position:
            self.calculate_and_buy()
        elif crossover(self.ema_slow, self.ema_fast) and self.position:
            self.position.close()

    @staticmethod
    def _ema(values, period: int):
        """지수 이동평균 계산"""
        series = pd.Series(values)
        return series.ewm(span=period, adjust=False).mean()


# ========================
# Strategy: RSI
# ========================

class RsiStrategy(PositionSizingMixin, Strategy):
    """RSI 기반 매매 전략 (과매도 구간 매수, 과매수 구간 또는 중립선 복귀 시 매도)"""

    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    position_size = 0.95

    def init(self):
        close = self.data.Close
        self.rsi = self.I(self._rsi, close, self.rsi_period)

    def _rsi(self, close: pd.Series, period: int) -> pd.Series:
        """RSI 계산"""
        close = pd.Series(close)
        delta = close.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()

        avg_loss = avg_loss.replace(0, np.finfo(float).eps)

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.fillna(50)

    def next(self):
        if len(self.rsi) > self.rsi_period:
            current_rsi = self.rsi[-1]

            if current_rsi < self.rsi_oversold and not self.position:
                self.calculate_and_buy()

            elif self.position:
                if current_rsi > self.rsi_overbought:
                    self.position.close()
                elif current_rsi >= 50 and len(self.rsi) > 1 and self.rsi[-2] < 50:
                    self.position.close()


# ========================
# Strategy: Bollinger Bands
# ========================

class BollingerBandsStrategy(PositionSizingMixin, Strategy):
    """볼린저 밴드 전략 (하단 밴드 이하 매수, 상단 밴드 또는 중심선 복귀 시 매도)"""

    period = 20
    std_dev = 2
    position_size = 0.95

    def init(self):
        close = self.data.Close
        self.sma = self.I(SMA, close, self.period)
        self.std = self.I(self._std, close, self.period)
        self.upper_band = self.I(lambda: self.sma + (self.std_dev * self.std))
        self.lower_band = self.I(lambda: self.sma - (self.std_dev * self.std))

    def _std(self, close: pd.Series, period: int) -> pd.Series:
        close = pd.Series(close)
        return close.rolling(window=period).std()

    def next(self):
        if len(self.data) < self.period:
            return

        if (len(self.upper_band) > 0 and len(self.lower_band) > 0 and
            not np.isnan(self.upper_band[-1]) and not np.isnan(self.lower_band[-1])):

            current_price = self.data.Close[-1]

            if current_price < self.lower_band[-1] and not self.position:
                self.calculate_and_buy()
            elif self.position:
                if current_price > self.upper_band[-1]:
                    self.position.close()
                elif current_price >= self.sma[-1] and len(self.sma) > 1:
                    self.position.close()


# ========================
# Strategy: MACD
# ========================

class MacdStrategy(PositionSizingMixin, Strategy):
    """MACD 전략 (MACD 선과 시그널 선의 교차로 매매)"""

    fast_period = 12
    slow_period = 26
    signal_period = 9
    position_size = 0.95

    def init(self):
        close = self.data.Close
        self.macd_line = self.I(self._macd_line, close, self.fast_period, self.slow_period)
        self.signal_line = self.I(self._signal_line, close, self.fast_period, self.slow_period, self.signal_period)

    def _macd_line(self, close: pd.Series, fast: int, slow: int) -> pd.Series:
        close = pd.Series(close)
        exp1 = close.ewm(span=fast).mean()
        exp2 = close.ewm(span=slow).mean()
        return exp1 - exp2

    def _signal_line(self, close: pd.Series, fast: int, slow: int, signal: int) -> pd.Series:
        macd = self._macd_line(close, fast, slow)
        return macd.ewm(span=signal).mean()

    def next(self):
        if (len(self.macd_line) > 1 and len(self.signal_line) > 1 and
            not np.isnan(self.macd_line[-1]) and not np.isnan(self.signal_line[-1])):

            if crossover(self.macd_line, self.signal_line) and not self.position:
                self.calculate_and_buy()
            elif crossover(self.signal_line, self.macd_line) and self.position:
                self.position.close()
