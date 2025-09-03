"""
RSI(Relative Strength Index) 전략
"""
import pandas as pd
import numpy as np
from backtesting import Strategy
from backtesting.lib import crossover, crossunder


class RSIStrategy(Strategy):
    """
    RSI 기반 매매 전략
    
    RSI가 oversold 수준 이하로 떨어지면 매수
    RSI가 overbought 수준 이상으로 올라가면 매도
    """
    
    # 전략 파라미터
    rsi_period = 14         # RSI 계산 기간
    rsi_oversold = 30       # 과매도 기준선
    rsi_overbought = 70     # 과매수 기준선
    position_size = 0.95    # 포지션 크기 (자본의 95% 사용)
    
    def init(self):
        """전략 초기화 - 지표 계산"""
        # RSI 계산
        self.rsi = self.I(self.RSI, self.data.Close, self.rsi_period)
        
    def next(self):
        """매 봉마다 실행되는 매매 로직"""
        # 현재 RSI 값
        current_rsi = self.rsi[-1]
        
        # 포지션이 없을 때 매수 신호 확인
        if not self.position:
            # RSI가 과매도 구간에 진입하면 매수
            if current_rsi < self.rsi_oversold:
                # 사용 가능한 현금의 95%로 매수
                self.buy(size=self.position_size)
        
        # 포지션이 있을 때 매도 신호 확인  
        elif self.position:
            # RSI가 과매수 구간에 진입하면 매도
            if current_rsi > self.rsi_overbought:
                # 모든 포지션 매도
                self.sell(size=self.position.size)
    
    @staticmethod
    def RSI(close_prices, period=14):
        """
        RSI(Relative Strength Index) 계산
        
        Args:
            close_prices: 종가 시계열 데이터
            period: RSI 계산 기간 (기본값: 14)
        
        Returns:
            RSI 값 시계열 (0-100 범위)
        """
        # 가격 변동 계산
        delta = pd.Series(close_prices).diff()
        
        # 상승분과 하락분 분리
        gain = delta.where(delta > 0, 0)  # 상승한 경우만 값 유지, 나머지는 0
        loss = -delta.where(delta < 0, 0)  # 하락한 경우만 절댓값으로 변환, 나머지는 0
        
        # 지수 이동평균으로 평균 상승분과 평균 하락분 계산
        avg_gain = gain.ewm(span=period).mean()
        avg_loss = loss.ewm(span=period).mean()
        
        # RS(Relative Strength) 계산
        rs = avg_gain / avg_loss
        
        # RSI 계산: RSI = 100 - (100 / (1 + RS))
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.values


class AggressiveRSIStrategy(Strategy):
    """
    보다 공격적인 RSI 전략
    더 넓은 RSI 범위와 부분 매매를 사용
    """
    
    rsi_period = 14
    rsi_oversold = 25       # 더 낮은 과매도 기준
    rsi_overbought = 75     # 더 높은 과매수 기준
    position_size = 1.0     # 100% 포지션
    
    def init(self):
        self.rsi = self.I(RSIStrategy.RSI, self.data.Close, self.rsi_period)
        
    def next(self):
        current_rsi = self.rsi[-1]
        
        if not self.position and current_rsi < self.rsi_oversold:
            self.buy(size=self.position_size)
        elif self.position and current_rsi > self.rsi_overbought:
            self.sell(size=self.position.size)


class ConservativeRSIStrategy(Strategy):
    """
    보수적인 RSI 전략
    더 좁은 RSI 범위와 작은 포지션 크기 사용
    """
    
    rsi_period = 14
    rsi_oversold = 35       # 더 높은 과매도 기준
    rsi_overbought = 65     # 더 낮은 과매수 기준
    position_size = 0.5     # 50% 포지션
    
    def init(self):
        self.rsi = self.I(RSIStrategy.RSI, self.data.Close, self.rsi_period)
        
    def next(self):
        current_rsi = self.rsi[-1]
        
        if not self.position and current_rsi < self.rsi_oversold:
            self.buy(size=self.position_size)
        elif self.position and current_rsi > self.rsi_overbought:
            self.sell(size=self.position.size)
