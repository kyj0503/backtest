"""
단순 이동평균 교차 전략 (SMA Crossover Strategy)

**역할**:
- backtesting.py의 Strategy 클래스를 상속하여 SMA 교차 전략 구현
- 단기 이동평균선이 장기 이동평균선을 상향/하향 돌파할 때 매매

**전략 로직**:
1. 골든 크로스(Golden Cross): 단기 MA가 장기 MA를 상향 돌파 → 매수 시그널
2. 데드 크로스(Death Cross): 단기 MA가 장기 MA를 하향 돌파 → 매도 시그널

**파라미터**:
- short_window: 단기 이동평균 기간 (기본값: 20일)
- long_window: 장기 이동평균 기간 (기본값: 50일)

**사용 예**:
- 20일선과 50일선의 교차로 매매
- 빠른 추세 전환 포착

**의존성**:
- backtesting.py: Strategy 베이스 클래스
- pandas: 이동평균 계산

**연관 컴포넌트**:
- Backend: app/services/backtest_service.py (전략 실행)
- Backend: app/services/strategy_service.py (파라미터 검증)
- Frontend: src/features/backtest/components/StrategySelector.tsx (전략 선택)
"""
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


class SMACrossStrategy(Strategy):
    """
    이동평균 교차 전략

    Parameters
    ----------
    sma_short : int
        단기 이동평균 기간 (기본값: 10)
    sma_long : int
        장기 이동평균 기간 (기본값: 20)
    position_size : float
        포지션 크기 (0.1 ~ 1.0, 기본값: 0.95)
    """

    # 전략 파라미터 정의
    sma_short = 10
    sma_long = 20
    position_size = 0.95

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


# 기존 SMAStrategy와의 호환성을 위한 별칭
SMAStrategy = SMACrossStrategy
