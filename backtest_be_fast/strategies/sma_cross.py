import pandas as pd
from backtesting import Strategy
from backtesting.lib import crossover

def SMA(values, n):
    """
    단순 이동평균(Simple Moving Average) 계산
    
    Parameters
    ----------
    values : pd.Series
        가격 데이터
    n : int
        이동평균 기간
        
    Returns
    -------
    pd.Series
        이동평균 값
    """
    return pd.Series(values).rolling(n).mean()

class SmaCross(Strategy):
    """
    이동평균 교차 전략
    
    Parameters
    ----------
    sma_short : int
        단기 이동평균 기간 (기본값: 10)
    sma_long : int
        장기 이동평균 기간 (기본값: 20)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.5)
    """
    
    # 전략 파라미터 정의
    sma_short = 10
    sma_long = 20
    position_size = 0.5
    
    def init(self):
        """
        전략 초기화
        - 이동평균 계산
        - 지표 등록
        """
        # 이동평균 계산
        self.sma1 = self.I(SMA, self.data.Close, self.sma_short)
        self.sma2 = self.I(SMA, self.data.Close, self.sma_long)
    
    def next(self):
        """
        각 봉마다 실행되는 전략 로직
        - 이동평균 교차 시 매수/매도 신호 생성
        - 포지션 크기 조절
        """
        # 포지션이 없을 때
        if not self.position:
            # 골든 크로스 (단기선이 장기선을 상향 돌파)
            if crossover(self.sma1, self.sma2):
                # 매수 가능한 수량 계산 (정수 단위로 반올림)
                price = self.data.Close[-1]
                size = int((self.equity * self.position_size) / price)
                if size > 0:  # 수량이 0보다 큰 경우에만 매수
                    self.buy(size=size)
        
        # 포지션이 있을 때
        else:
            # 데드 크로스 (단기선이 장기선을 하향 돌파)
            if crossover(self.sma2, self.sma1):
                self.position.close() 