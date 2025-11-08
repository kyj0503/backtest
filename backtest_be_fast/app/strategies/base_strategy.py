"""
기본 전략 Mixin (Base Strategy Mixin)

**역할**:
- 모든 매매 전략에서 공통으로 사용하는 위치 조정 로직 제공
- 매수 로직 중복 제거
- 일관된 포지션 크기 계산

**주요 기능**:
1. calculate_and_buy(): 주어진 가격에서 계산된 수량으로 매수
2. position_size: 조정 가능한 포지션 크기 파라미터

**사용 예**:
```python
class MyStrategy(PositionSizingMixin, Strategy):
    position_size = 0.95

    def next(self):
        if should_buy:
            self.calculate_and_buy()
```

**의존성**:
- backtesting.py: Strategy 베이스 클래스

**연관 컴포넌트**:
- Backend: app/strategies/*.py (모든 기술적 전략)
"""
from backtesting import Strategy


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

        Examples
        --------
        >>> # 현재 종가로 매수
        >>> self.calculate_and_buy()

        >>> # 특정 가격으로 매수
        >>> self.calculate_and_buy(price=1000.0)
        """
        # 가격이 제공되지 않으면 현재 종가 사용
        if price is None:
            price = self.data.Close[-1]

        # 포지션 크기만큼 구매 가능한 주식 수 계산 (정수 단위)
        size = int((self.equity * self.position_size) / price)

        # 0개 이상의 주식만 매수 가능
        if size > 0:
            self.buy(size=size)
