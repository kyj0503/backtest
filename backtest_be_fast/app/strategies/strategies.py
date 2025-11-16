"""
백테스팅 전략 모음 (Backtesting Strategies Collection)

**역할**:
- backtesting.py 라이브러리를 위한 모든 기술 전략 및 기본 전략 구현
- 위치 조정 로직의 Mixin 제공
- 다양한 매매 신호 기반의 전략 6가지

**포함된 전략**:
1. PositionSizingMixin - 공통 위치 조정 로직
2. BuyAndHoldStrategy - 매수 후 보유 전략
3. SMACrossStrategy - 이동평균 교차 전략
4. EMAStrategy - 지수 이동평균 교차 전략
5. RSIStrategy - 상대강도지수 기반 전략
6. BollingerBandsStrategy - 볼린저 밴드 기반 전략
7. MACDStrategy - MACD 교차 전략

**통화 정책**:
- DB 저장: 원본 통화 (KRW, JPY, EUR, GBP 등)
- 백테스트 계산: 모든 가격을 USD로 변환
- 프론트엔드 표시: 개별 종목은 원본 통화, 결과는 USD

**파라미터**:
- position_size: 포지션 크기 (0.0 ~ 1.0, 기본값: 0.95)
- 전략별 지표 파라미터 (sma_short, rsi_period, 등)

**의존성**:
- backtesting.py: Strategy 베이스 클래스
- pandas: 데이터 처리 및 이동평균 계산
- numpy: 수치 계산

**연관 컴포넌트**:
- Backend: app/services/strategy_service.py (전략 관리)
- Backend: app/services/backtest_service.py (백테스트 실행)
- Frontend: src/features/backtest/components/StrategySelector.tsx (전략 선택)
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
    """
    위치 조정(Position Sizing) 기능을 제공하는 Mixin

    모든 매매 전략에서 공통으로 사용하는 위치 조정 로직을 제공합니다.
    포지션 크기는 configurable하며, 기본값은 0.95(95%)입니다.
    """

    # 포지션 크기 (0.0 ~ 1.0, 기본값: 0.95)
    position_size = 0.95

    def calculate_and_buy(self, price=None):
        """
        주어진 가격에서 계산된 수량으로 매수합니다.

        포지션 크기에 따라 매수 가능한 주식 수를 계산하고,
        0개보다 많은 경우에만 실제 매수를 실행합니다.

        Parameters
        ----------
        price : float, optional
            매수 가격. None이면 현재 종가(Close[-1])를 사용합니다.

        Returns
        -------
        None
        """
        # 가격이 제공되지 않으면 현재 종가 사용
        if price is None:
            price = self.data.Close[-1]

        # 포지션 크기만큼 구매 가능한 주식 수 계산 (정수 단위)
        size = int((self.equity * self.position_size) / price)

        # 0개 이상의 주식만 매수 가능
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
    """
    이동평균 교차 전략

    단기 이동평균선이 장기 이동평균선을 상향/하향 돌파할 때 매매

    Parameters
    ----------
    sma_short : int
        단기 이동평균 기간 (기본값: 10)
    sma_long : int
        장기 이동평균 기간 (기본값: 20)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    sma_short = 10
    sma_long = 20
    position_size = 0.95

    def init(self):
        """이동평균 계산 및 지표 등록"""
        self.sma1 = self.I(_sma_helper, self.data.Close, self.sma_short)
        self.sma2 = self.I(_sma_helper, self.data.Close, self.sma_long)

    def next(self):
        """각 봉마다 실행되는 전략 로직"""
        if not self.position:
            # 골든 크로스 (단기선이 장기선을 상향 돌파)
            if crossover(self.sma1, self.sma2):
                self.calculate_and_buy()
        else:
            # 데드 크로스 (단기선이 장기선을 하향 돌파)
            if crossover(self.sma2, self.sma1):
                self.position.close()


# ========================
# Strategy: EMA Crossover
# ========================

class EmaStrategy(PositionSizingMixin, Strategy):
    """EMA 교차 전략

    지수 이동평균(EMA) 교차를 사용한 추세 추종 전략
    최근 가격에 더 높은 가중치를 부여하는 이동평균

    Parameters
    ----------
    fast_window : int
        단기 EMA 기간 (기본값: 12)
    slow_window : int
        장기 EMA 기간 (기본값: 26)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    fast_window = 12
    slow_window = 26
    position_size = 0.95

    def init(self):
        close = self.data.Close
        self.ema_fast = self.I(self._ema, close, self.fast_window)
        self.ema_slow = self.I(self._ema, close, self.slow_window)

    def next(self):
        # 빠른 EMA가 느린 EMA를 상향 돌파: 골든크로스 → 매수
        if crossover(self.ema_fast, self.ema_slow) and not self.position:
            self.calculate_and_buy()
        # 빠른 EMA가 느린 EMA를 하향 돌파: 데드크로스 → 매도
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
    """RSI 기반 매매 전략

    RSI(Relative Strength Index) 지표를 사용하여 과매도/과매수 구간에서 매매하는 전략

    Parameters
    ----------
    rsi_period : int
        RSI 계산 기간 (기본값: 14)
    rsi_overbought : int
        과매수 기준선 (기본값: 70)
    rsi_oversold : int
        과매도 기준선 (기본값: 30)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    rsi_period = 14
    rsi_overbought = 70
    rsi_oversold = 30
    position_size = 0.95

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

            # 포지션이 없을 때: RSI 과매도 구간에서 매수
            if current_rsi < self.rsi_oversold and not self.position:
                self.calculate_and_buy()

            # 포지션이 있을 때: RSI 과매수 구간 또는 중립선(50) 복귀 시 매도
            elif self.position:
                # 방법 1: 과매수 구간 도달 시 매도
                if current_rsi > self.rsi_overbought:
                    self.position.close()
                # 방법 2: RSI가 중립선(50)을 상향 돌파하면 매도 (이익 실현)
                # 과매도에서 매수했으므로, 50 이상 회복 시 수익 실현이 합리적
                elif current_rsi >= 50 and len(self.rsi) > 1 and self.rsi[-2] < 50:
                    self.position.close()


# ========================
# Strategy: Bollinger Bands
# ========================

class BollingerBandsStrategy(PositionSizingMixin, Strategy):
    """볼린저 밴드 전략

    볼린저 밴드를 사용한 변동성 기반 매매 전략
    가격이 밴드 경계를 돌파할 때 매매

    Parameters
    ----------
    period : int
        이동평균 기간 (기본값: 20)
    std_dev : int
        표준편차 배수 (기본값: 2)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    period = 20
    std_dev = 2
    position_size = 0.95

    def init(self):
        close = self.data.Close
        # 중심선 (SMA) 계산
        self.sma = self.I(SMA, close, self.period)
        # 표준편차 계산
        self.std = self.I(self._std, close, self.period)
        # 상단/하단 밴드 계산 (SMA와 STD 재사용)
        self.upper_band = self.I(lambda: self.sma + (self.std_dev * self.std))
        self.lower_band = self.I(lambda: self.sma - (self.std_dev * self.std))

    def _std(self, close: pd.Series, period: int) -> pd.Series:
        """표준편차 계산"""
        close = pd.Series(close)
        return close.rolling(window=period).std()

    def next(self):
        if len(self.data) < self.period:
            return

        if (len(self.upper_band) > 0 and len(self.lower_band) > 0 and
            not np.isnan(self.upper_band[-1]) and not np.isnan(self.lower_band[-1])):

            current_price = self.data.Close[-1]

            # 가격이 하단 밴드 아래로 떨어짐: 과매도 → 매수
            if current_price < self.lower_band[-1] and not self.position:
                self.calculate_and_buy()
            # 가격이 상단 밴드 위로 올라감 또는 중심선(SMA) 복귀: 매도
            elif self.position:
                if current_price > self.upper_band[-1]:
                    # 과매수 구간: 매도
                    self.position.close()
                elif current_price >= self.sma[-1] and len(self.sma) > 1:
                    # 하단에서 매수했으므로 중심선 복귀 시 이익 실현
                    self.position.close()


# ========================
# Strategy: MACD
# ========================

class MacdStrategy(PositionSizingMixin, Strategy):
    """MACD 전략

    MACD 지표를 사용한 추세 추종 및 모멘텀 전략
    MACD 선과 시그널 선의 교차로 매매

    Parameters
    ----------
    fast_period : int
        단기 EMA 기간 (기본값: 12)
    slow_period : int
        장기 EMA 기간 (기본값: 26)
    signal_period : int
        시그널 EMA 기간 (기본값: 9)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    fast_period = 12
    slow_period = 26
    signal_period = 9
    position_size = 0.95

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

            # MACD 선이 시그널 선을 상향 돌파: 매수
            if crossover(self.macd_line, self.signal_line) and not self.position:
                self.calculate_and_buy()
            # MACD 선이 시그널 선을 하향 돌파: 매도
            elif crossover(self.signal_line, self.macd_line) and self.position:
                self.position.close()
