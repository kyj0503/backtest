"""
매수 후 보유 전략 (Buy and Hold Strategy)

**역할**:
- backtesting.py의 Strategy 클래스를 상속하여 Buy & Hold 전략 구현
- 가장 단순한 전략: 첫 시점에 매수하고 끝까지 보유

**전략 로직**:
1. 백테스트 시작 시점에 전액 매수
2. 백테스트 종료 시까지 보유 (매도 없음)

**파라미터**:
- 없음 (파라미터 필요 없는 전략)

**특징**:
- 시장 타이밍을 시도하지 않음
- 거래 비용 최소화 (1회만 매수)
- 장기 투자 벤치마크로 자주 사용됨

**사용 사례**:
- 다른 전략과 성과 비교를 위한 베이스라인
- 장기 투자 시뮬레이션

**의존성**:
- backtesting.py: Strategy 베이스 클래스

**연관 컴포넌트**:
- Backend: app/services/portfolio_service.py (포트폴리오 Buy & Hold)
- Frontend: src/features/backtest/components/StrategySelector.tsx (기본 전략)
"""
from backtesting import Strategy


class BuyAndHoldStrategy(Strategy):
    """매수 후 보유 전략"""
    
    def init(self):
        self.bought = False
    
    def next(self):
        if not self.bought:
            self.buy()
            self.bought = True
