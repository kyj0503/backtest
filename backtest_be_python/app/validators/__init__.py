"""
Validators 패키지

**역할**:
- 비즈니스 규칙 검증 로직 중앙화
- Pydantic 스키마와 서비스 레이어 사이의 검증 담당

**구조**:
- date_validator.py: 날짜 검증 (BacktestValidator가 사용)
- symbol_validator.py: 티커/심볼 검증 (BacktestValidator가 사용)
- backtest_validator.py: 단일 종목 백테스트 요청 검증
  (app/services/validation_service.py를 통해 사용됨)

**P2-04 (배치5) 변경사항**:
portfolio_validator.py(PortfolioValidator)는 삭제했다. grep으로 확인한 결과 이
패키지의 재export 외에는 어디에서도 import되지 않는 죽은 코드였고, 그 결과
포트폴리오 백테스트 경로에는 rebalance_frequency 멤버십 검증과 미래 날짜 검증이
빠져 있었으며 PortfolioStock.symbol의 field_validator에는 필드 선언 순서 버그가
있었다(asset_type='cash' 우회 분기가 실행되지 않음). 이 규칙들은 죽은
PortfolioValidator를 고쳐서 새로 연결하는 대신, 실제로 사용되는
app/schemas/schemas.py(PortfolioStock, PortfolioBacktestRequest)와
app/api/v1/endpoints/backtest.py(최소 기간)로 통합했다. 자세한 내용은
app/schemas/schemas.py 모듈 docstring 참고.

**사용 패턴**:
```python
from app.validators import (
    DateValidator,
    SymbolValidator,
    BacktestValidator,
)

date_validator = DateValidator()
date_validator.validate_date_range(start, end)

symbol_validator = SymbolValidator(data_fetcher)
ticker = symbol_validator.validate_and_normalize("aapl")

backtest_validator = BacktestValidator(data_fetcher, strategy_service)
backtest_validator.validate_request(backtest_request)
```
"""
from .date_validator import DateValidator
from .symbol_validator import SymbolValidator
from .backtest_validator import BacktestValidator

__all__ = [
    'DateValidator',
    'SymbolValidator',
    'BacktestValidator',
]
