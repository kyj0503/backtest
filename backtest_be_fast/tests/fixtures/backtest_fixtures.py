"""
Backtest Test Fixtures

백테스트 관련 테스트 데이터 팩토리와 fixtures
"""

import factory
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from faker import Faker

fake = Faker()


# ============================================================================
# Factory Classes
# ============================================================================

class BacktestRequestFactory(factory.Factory):
    """백테스트 요청 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    symbol = factory.Faker('random_element', elements=['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'])
    start_date = factory.LazyFunction(
        lambda: (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    )
    end_date = factory.LazyFunction(
        lambda: datetime.now().strftime("%Y-%m-%d")
    )
    initial_capital = factory.LazyFunction(
        lambda: float(fake.pydecimal(left_digits=5, right_digits=2, positive=True))
    )
    strategy = factory.Faker('random_element', elements=['buy_and_hold', 'sma_cross', 'rsi_strategy'])
    parameters = factory.Dict({})


class BacktestResultFactory(factory.Factory):
    """백테스트 결과 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    success = True
    metrics = factory.Dict({
        'total_return': factory.LazyFunction(lambda: float(fake.pydecimal(left_digits=1, right_digits=4, positive=True))),
        'annual_return': factory.LazyFunction(lambda: float(fake.pydecimal(left_digits=1, right_digits=4))),
        'sharpe_ratio': factory.LazyFunction(lambda: float(fake.pydecimal(left_digits=1, right_digits=2))),
        'max_drawdown': factory.LazyFunction(lambda: float(fake.pydecimal(left_digits=1, right_digits=4, positive=False))),
        'win_rate': factory.LazyFunction(lambda: float(fake.pydecimal(left_digits=1, right_digits=4, positive=True, max_value=1))),
    })
    equity_curve = factory.List([])
    trades = factory.List([])


class BacktestHistoryFactory(factory.Factory):
    """백테스트 히스토리 데이터 팩토리"""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Faker('random_int', min=1, max=100)
    symbol = factory.Faker('random_element', elements=['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
    strategy = factory.Faker('random_element', elements=['buy_and_hold', 'sma_cross', 'rsi_strategy'])
    start_date = factory.LazyFunction(
        lambda: (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    )
    end_date = factory.LazyFunction(
        lambda: datetime.now().strftime("%Y-%m-%d")
    )
    initial_capital = factory.LazyFunction(
        lambda: float(fake.pydecimal(left_digits=5, right_digits=2, positive=True))
    )
    final_value = factory.LazyAttribute(
        lambda obj: obj.initial_capital * (1 + fake.pyfloat(min_value=-0.5, max_value=2.0))
    )
    total_return = factory.LazyAttribute(
        lambda obj: (obj.final_value - obj.initial_capital) / obj.initial_capital
    )
    created_at = factory.LazyFunction(datetime.now)


# ============================================================================
# Helper Functions
# ============================================================================

def create_backtest_request_data(
    symbol: str = "AAPL",
    start_date: str = None,
    end_date: str = None,
    initial_capital: float = 10000.0,
    strategy: str = "buy_and_hold",
    parameters: Dict[str, Any] = None
) -> Dict[str, Any]:
    """백테스트 요청 데이터 생성"""
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    if end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")
    
    if parameters is None:
        parameters = {}
    
    return {
        "symbol": symbol,
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": initial_capital,
        "strategy": strategy,
        "parameters": parameters
    }


def create_price_data(
    symbol: str = "AAPL",
    start_date: datetime = None,
    days: int = 30
) -> List[Dict[str, Any]]:
    """가격 데이터 생성"""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=days)
    
    price_data = []
    current_price = 150.0
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        # 랜덤한 가격 변동 (±5%)
        change = fake.pyfloat(min_value=-0.05, max_value=0.05)
        current_price = current_price * (1 + change)
        
        open_price = current_price * fake.pyfloat(min_value=0.98, max_value=1.02)
        high_price = max(open_price, current_price) * fake.pyfloat(min_value=1.0, max_value=1.03)
        low_price = min(open_price, current_price) * fake.pyfloat(min_value=0.97, max_value=1.0)
        close_price = current_price
        volume = fake.random_int(min=1000000, max=10000000)
        
        price_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "volume": volume
        })
    
    return price_data


def create_equity_curve(
    initial_capital: float = 10000.0,
    days: int = 30,
    growth_rate: float = 0.10  # 연 10% 성장
) -> List[Dict[str, Any]]:
    """자본 곡선 데이터 생성"""
    equity_curve = []
    current_value = initial_capital
    daily_growth = (1 + growth_rate) ** (1 / 252) - 1  # 연간 성장률을 일간으로 변환
    
    start_date = datetime.now() - timedelta(days=days)
    
    for i in range(days):
        date = start_date + timedelta(days=i)
        
        # 랜덤한 변동성 추가
        volatility = fake.pyfloat(min_value=-0.03, max_value=0.03)
        current_value = current_value * (1 + daily_growth + volatility)
        
        equity_curve.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": round(current_value, 2)
        })
    
    return equity_curve


def create_trade_data(
    symbol: str = "AAPL",
    num_trades: int = 10
) -> List[Dict[str, Any]]:
    """거래 데이터 생성"""
    trades = []
    start_date = datetime.now() - timedelta(days=365)
    
    for i in range(num_trades):
        entry_date = start_date + timedelta(days=fake.random_int(min=0, max=300))
        exit_date = entry_date + timedelta(days=fake.random_int(min=1, max=30))
        
        entry_price = fake.pyfloat(min_value=100.0, max_value=200.0)
        exit_price = entry_price * fake.pyfloat(min_value=0.9, max_value=1.15)
        quantity = fake.random_int(min=10, max=100)
        
        pnl = (exit_price - entry_price) * quantity
        pnl_percent = (exit_price - entry_price) / entry_price
        
        trades.append({
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "exit_date": exit_date.strftime("%Y-%m-%d"),
            "symbol": symbol,
            "side": fake.random_element(elements=["LONG", "SHORT"]),
            "quantity": quantity,
            "entry_price": round(entry_price, 2),
            "exit_price": round(exit_price, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_percent, 4),
            "status": "CLOSED"
        })
    
    return trades


def create_backtest_metrics(
    total_return: float = 0.25,
    sharpe_ratio: float = 1.5,
    max_drawdown: float = -0.15
) -> Dict[str, Any]:
    """백테스트 메트릭 데이터 생성"""
    return {
        "total_return": total_return,
        "annual_return": total_return / 1.0,  # 1년 기준
        "sharpe_ratio": sharpe_ratio,
        "sortino_ratio": sharpe_ratio * 1.2,  # 일반적으로 샤프보다 높음
        "max_drawdown": max_drawdown,
        "max_drawdown_duration": fake.random_int(min=5, max=30),
        "win_rate": fake.pyfloat(min_value=0.4, max_value=0.7),
        "profit_factor": fake.pyfloat(min_value=1.0, max_value=3.0),
        "avg_trade_return": total_return / 10,  # 평균 10개 거래 가정
        "num_trades": fake.random_int(min=5, max=50),
        "num_winning_trades": fake.random_int(min=3, max=30),
        "num_losing_trades": fake.random_int(min=2, max=20),
    }


# ============================================================================
# Pytest Fixtures (conftest.py에서 import하여 사용)
# ============================================================================

def sample_backtest_request_fixture():
    """샘플 백테스트 요청 fixture"""
    return BacktestRequestFactory()


def sample_backtest_result_fixture():
    """샘플 백테스트 결과 fixture"""
    return BacktestResultFactory()


def sample_backtest_history_fixture():
    """샘플 백테스트 히스토리 fixture"""
    return BacktestHistoryFactory()
