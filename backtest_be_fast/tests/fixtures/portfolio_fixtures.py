"""
Portfolio Test Fixtures

포트폴리오 관련 테스트 데이터 팩토리와 fixtures
"""

import factory
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


# ============================================================================
# Factory Classes
# ============================================================================

class PortfolioFactory(factory.Factory):
    """포트폴리오 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    initial_cash = factory.LazyFunction(
        lambda: float(fake.pydecimal(left_digits=5, right_digits=2, positive=True))
    )
    cash = factory.LazyAttribute(lambda obj: obj.initial_cash)
    positions = factory.List([])
    trades = factory.List([])


class PositionFactory(factory.Factory):
    """포지션 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    symbol = factory.Faker('random_element', elements=['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    quantity = factory.Faker('random_int', min=10, max=100)
    entry_price = factory.LazyFunction(
        lambda: float(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
    )
    current_price = factory.LazyAttribute(
        lambda obj: obj.entry_price * fake.pyfloat(min_value=0.8, max_value=1.2)
    )
    entry_date = factory.LazyFunction(
        lambda: datetime.now().strftime("%Y-%m-%d")
    )
    pnl = factory.LazyAttribute(
        lambda obj: (obj.current_price - obj.entry_price) * obj.quantity
    )
    pnl_percent = factory.LazyAttribute(
        lambda obj: (obj.current_price - obj.entry_price) / obj.entry_price
    )


class TradeFactory(factory.Factory):
    """거래 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    symbol = factory.Faker('random_element', elements=['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    side = factory.Faker('random_element', elements=['BUY', 'SELL'])
    quantity = factory.Faker('random_int', min=10, max=100)
    price = factory.LazyFunction(
        lambda: float(fake.pydecimal(left_digits=3, right_digits=2, positive=True))
    )
    timestamp = factory.LazyFunction(datetime.now)
    commission = factory.LazyAttribute(
        lambda obj: obj.price * obj.quantity * 0.001  # 0.1% 수수료
    )


# ============================================================================
# Helper Functions
# ============================================================================

def create_portfolio_data(
    initial_cash: float = 10000.0,
    positions: List[Dict[str, Any]] = None,
    trades: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """포트폴리오 데이터 생성"""
    if positions is None:
        positions = []
    
    if trades is None:
        trades = []
    
    # 포지션 가치 계산
    total_position_value = sum(
        pos.get('quantity', 0) * pos.get('current_price', 0)
        for pos in positions
    )
    
    # 거래로 사용된 현금 계산
    cash_used = sum(
        trade.get('quantity', 0) * trade.get('price', 0) + trade.get('commission', 0)
        for trade in trades
        if trade.get('side') == 'BUY'
    )
    
    cash_received = sum(
        trade.get('quantity', 0) * trade.get('price', 0) - trade.get('commission', 0)
        for trade in trades
        if trade.get('side') == 'SELL'
    )
    
    current_cash = initial_cash - cash_used + cash_received
    
    return {
        "initial_cash": initial_cash,
        "cash": max(0, current_cash),
        "positions": positions,
        "trades": trades,
        "total_value": current_cash + total_position_value
    }


def create_position_data(
    symbol: str = "AAPL",
    quantity: int = 10,
    entry_price: float = 150.0,
    current_price: float = None
) -> Dict[str, Any]:
    """포지션 데이터 생성"""
    if current_price is None:
        current_price = entry_price * fake.pyfloat(min_value=0.9, max_value=1.1)
    
    pnl = (current_price - entry_price) * quantity
    pnl_percent = (current_price - entry_price) / entry_price
    
    return {
        "symbol": symbol,
        "quantity": quantity,
        "entry_price": entry_price,
        "current_price": current_price,
        "entry_date": datetime.now().strftime("%Y-%m-%d"),
        "pnl": round(pnl, 2),
        "pnl_percent": round(pnl_percent, 4),
        "market_value": round(current_price * quantity, 2)
    }


def create_trade_data(
    symbol: str = "AAPL",
    side: str = "BUY",
    quantity: int = 10,
    price: float = 150.0,
    commission_rate: float = 0.001
) -> Dict[str, Any]:
    """거래 데이터 생성"""
    commission = price * quantity * commission_rate
    total_value = price * quantity
    
    if side == "BUY":
        total_cost = total_value + commission
    else:  # SELL
        total_cost = total_value - commission
    
    return {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.now().isoformat(),
        "commission": round(commission, 2),
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2)
    }


def create_multiple_positions(
    num_positions: int = 3,
    total_investment: float = 10000.0
) -> List[Dict[str, Any]]:
    """여러 포지션 데이터 생성"""
    symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    positions = []
    
    investment_per_position = total_investment / num_positions
    
    for i in range(num_positions):
        symbol = fake.random_element(elements=symbols)
        entry_price = fake.pyfloat(min_value=100.0, max_value=300.0)
        quantity = int(investment_per_position / entry_price)
        current_price = entry_price * fake.pyfloat(min_value=0.8, max_value=1.2)
        
        positions.append(create_position_data(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price
        ))
    
    return positions


def create_trade_history(
    num_trades: int = 20,
    symbols: List[str] = None
) -> List[Dict[str, Any]]:
    """거래 히스토리 생성"""
    if symbols is None:
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
    
    trades = []
    
    for i in range(num_trades):
        symbol = fake.random_element(elements=symbols)
        side = fake.random_element(elements=['BUY', 'SELL'])
        quantity = fake.random_int(min=10, max=100)
        price = fake.pyfloat(min_value=100.0, max_value=300.0)
        
        trades.append(create_trade_data(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price
        ))
    
    return trades


def calculate_portfolio_metrics(portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """포트폴리오 메트릭 계산"""
    initial_cash = portfolio.get('initial_cash', 0)
    total_value = portfolio.get('total_value', initial_cash)
    
    total_return = (total_value - initial_cash) / initial_cash if initial_cash > 0 else 0
    
    positions = portfolio.get('positions', [])
    total_pnl = sum(pos.get('pnl', 0) for pos in positions)
    
    winning_positions = [pos for pos in positions if pos.get('pnl', 0) > 0]
    losing_positions = [pos for pos in positions if pos.get('pnl', 0) < 0]
    
    return {
        "total_value": total_value,
        "total_return": round(total_return, 4),
        "total_pnl": round(total_pnl, 2),
        "num_positions": len(positions),
        "num_winning_positions": len(winning_positions),
        "num_losing_positions": len(losing_positions),
        "win_rate": len(winning_positions) / len(positions) if positions else 0,
        "cash_allocation": portfolio.get('cash', 0) / total_value if total_value > 0 else 0
    }


# ============================================================================
# Pytest Fixtures
# ============================================================================

def sample_portfolio_fixture():
    """샘플 포트폴리오 fixture"""
    return PortfolioFactory()


def sample_position_fixture():
    """샘플 포지션 fixture"""
    return PositionFactory()


def sample_trade_fixture():
    """샘플 거래 fixture"""
    return TradeFactory()
