"""
Validators 패키지

**역할**:
- 비즈니스 규칙 검증 로직 중앙화
- Pydantic 스키마와 서비스 레이어 사이의 검증 담당

**구조**:
- date_validator.py: 날짜 검증
- symbol_validator.py: 티커/심볼 검증
- backtest_validator.py: 백테스트 요청 검증
- portfolio_validator.py: 포트폴리오 요청 검증

**사용 패턴**:
```python
from app.validators import (
    DateValidator,
    SymbolValidator,
    BacktestValidator,
    PortfolioValidator
)

date_validator = DateValidator()
date_validator.validate_date_range(start, end)

symbol_validator = SymbolValidator(data_fetcher)
ticker = symbol_validator.validate_and_normalize("aapl")

backtest_validator = BacktestValidator(data_fetcher, strategy_service)
backtest_validator.validate_request(backtest_request)

portfolio_validator = PortfolioValidator(data_fetcher)
portfolio_validator.validate_request(portfolio_request)
```
"""
from .date_validator import DateValidator
from .symbol_validator import SymbolValidator
from .backtest_validator import BacktestValidator
from .portfolio_validator import PortfolioValidator

__all__ = [
    'DateValidator',
    'SymbolValidator',
    'BacktestValidator',
    'PortfolioValidator',
]
