# Domain-Driven Design 아키텍처 가이드

> 상태: 제안/부분 적용 문서. 본 문서는 설계 방향을 설명하며, 예시 경로의 `app/domains/*` 구조는 점진 도입 대상입니다. 현재 구현은 주로 `backend/app/services/*` 계층에 존재합니다.

Phase 3에서 설계된 Domain-Driven Design (DDD) 아키텍처에 대한 가이드입니다.

정합성 메모:
- 본 도메인 계층은 점진적으로 도입되는 중이며, 현재 API 경로는 서비스 계층(예: `backend/app/services/backtest/*`, `backend/app/services/*.py`)이 중심입니다.
- 문서의 예시 경로와 실제 파일 구조는 상기 상태를 전제로 읽어 주세요.

## 개요

백테스팅 시스템을 3개의 핵심 도메인으로 분리하여 비즈니스 로직을 명확하게 구조화했습니다:

- **Backtest Domain**: 백테스트 실행 및 전략 관리
- **Portfolio Domain**: 자산 배분 및 포트폴리오 최적화  
- **Data Domain**: 시장 데이터 수집 및 관리

## 도메인 구조

### 1. Backtest Domain (`app/domains/backtest/`)

백테스트 실행, 전략 관리, 성과 분석을 담당하는 핵심 도메인입니다.

#### Value Objects (불변 값 객체)

**DateRange** (`value_objects/date_range.py`)
```python
from app.domains.backtest.value_objects.date_range import DateRange

# 날짜 범위 생성 및 검증
date_range = DateRange(start_date="2023-01-01", end_date="2023-12-31")
print(date_range.duration_days())  # 364
print(date_range.is_valid())       # True
```

**PerformanceMetrics** (`value_objects/performance_metrics.py`)
```python
from app.domains.backtest.value_objects.performance_metrics import PerformanceMetrics

# 성과 지표 계산
metrics = PerformanceMetrics(
    total_return=0.15,
    annual_return=0.12,
    volatility=0.18,
    sharpe_ratio=0.85,
    max_drawdown=-0.08
)
print(metrics.format_metrics())  # 포맷된 성과 지표 출력
```

#### Entities (엔티티)

**BacktestResultEntity** (`entities/backtest_result.py`)
```python
from app.domains.backtest.entities.backtest_result import BacktestResultEntity

# 백테스트 결과 생성
result = BacktestResultEntity(
    result_id="bt_001",
    strategy_name="SMA Crossover",
    metrics=performance_metrics,
    date_range=date_range
)
result.is_successful()  # 성공 여부 확인
```

#### Domain Services (도메인 서비스)

**BacktestDomainService** (`services/backtest_domain_service.py`)
```python
from app.domains.backtest.services.backtest_domain_service import BacktestDomainService

# 백테스트 결과 생성
backtest_service = BacktestDomainService()
result = backtest_service.generate_backtest_result(
    result_id="bt_001",
    symbol="AAPL",
    strategy="SMA",
    total_return=0.15,
    annual_return=0.12
)
```

### 2. Portfolio Domain (`app/domains/portfolio/`)

자산 배분, 포트폴리오 관리, 리밸런싱을 담당하는 도메인입니다.

#### Value Objects

**Weight** (`value_objects/weight.py`)
```python
from app.domains.portfolio.value_objects.weight import Weight

# 포트폴리오 가중치 관리
weight = Weight(Decimal('0.6'))  # 60%
percentage = weight.to_percentage()  # 60.0
is_valid = weight.is_valid()         # True (0-1 범위 검증)
```

**Allocation** (`value_objects/allocation.py`)
```python
from app.domains.portfolio.value_objects.allocation import Allocation

# 자산 배분 분석
allocation = Allocation({'AAPL': Decimal('0.6'), 'CASH': Decimal('0.4')})
diversity_score = allocation.calculate_diversification_score()  # 0.52 (허핀달 지수)
is_balanced = allocation.is_well_diversified()                   # True
```

#### Entities

**PortfolioEntity** (`entities/portfolio_entity.py`)
```python
from app.domains.portfolio.entities.portfolio_entity import PortfolioEntity

# 포트폴리오 생성 및 관리
portfolio = PortfolioEntity(
    portfolio_id="port_001",
    name="성장 포트폴리오",
    assets=[asset1, asset2]
)
portfolio.add_asset(asset3)
portfolio.rebalance()  # 리밸런싱 실행
```

#### Domain Services

**PortfolioDomainService** (`services/portfolio_domain_service.py`)
```python
from app.domains.portfolio.services.portfolio_domain_service import PortfolioDomainService

# 포트폴리오 최적화
portfolio_service = PortfolioDomainService()

# 변동성 기반 최적화
optimized_weights = portfolio_service.optimize_portfolio(assets, risk_tolerance=0.8)

# 상관관계 분석
correlation_matrix = portfolio_service.calculate_correlation_matrix(assets)
```

### 3. Data Domain (`app/domains/data/`)

시장 데이터 수집, 캐싱, 무결성 관리를 담당하는 도메인입니다.

#### Value Objects

**Price** (`value_objects/price.py`)
```python
from app.domains.data.value_objects.price import Price

# 가격 정보 관리
price = Price(Decimal('150.00'), 'USD')
formatted = price.format()           # "USD 150.00"
change = price.calculate_change(140) # 7.14% 증가
```

**Symbol** (`value_objects/symbol.py`)
```python
from app.domains.data.value_objects.symbol import Symbol

# 심볼 정보 관리
symbol = Symbol('AAPL', 'stock')
display_name = symbol.get_display_name()  # "AAPL (Stock)"
is_cash = symbol.is_cash_asset()          # False
```

#### Domain Services

**DataDomainService** (`services/data_domain_service.py`)
```python
from app.domains.data.services.data_domain_service import DataDomainService

# 데이터 분석 및 검증
data_service = DataDomainService()

# 상관관계 계산
correlation = data_service.calculate_correlation(asset1_data, asset2_data)

# 데이터 일관성 검증
is_consistent = data_service.validate_data_consistency(market_data)
```

## 고급 비즈니스 기능

### 포트폴리오 최적화

변동성을 고려한 리스크 조정 포트폴리오 가중치 계산:

```python
# 리스크 허용도에 따른 최적화
risk_tolerance = 0.8  # 높은 리스크 허용
optimized_weights = portfolio_service.optimize_portfolio(assets, risk_tolerance)

# 결과: {'AAPL': 0.85, 'CASH': 0.15} - 공격적 포트폴리오
```

### 다변화 분석

허핀달 지수를 활용한 포트폴리오 집중도 측정:

```python
# 다변화 점수 계산 (0: 완전 집중, 1: 완전 분산)
allocation = Allocation({'AAPL': 0.4, 'GOOGL': 0.3, 'MSFT': 0.3})
diversity_score = allocation.calculate_diversification_score()  # 0.74
```

### 상관관계 분석

자산 간 상관계수 매트릭스 계산:

```python
# 포트폴리오 내 자산 간 상관관계
correlation_matrix = portfolio_service.calculate_correlation_matrix([
    asset_aapl, asset_googl, asset_cash
])
# 결과: AAPL-GOOGL: 0.85, AAPL-CASH: 0.0, GOOGL-CASH: 0.0
```

### 데이터 무결성 검증

시계열 데이터 일관성 및 이상치 탐지:

```python
# 데이터 품질 검증
market_data = MarketDataEntity(symbol="AAPL", data_points=daily_prices)
is_valid = data_service.validate_data_consistency(market_data)

# 이상치 탐지 및 정제
cleaned_data = data_service.detect_outliers(market_data)
```

## DDD 전술적 패턴 활용

### Value Objects (값 객체)

- **불변성**: 생성 후 수정 불가능
- **등가성**: 값으로 동등성 판단
- **자체 검증**: 생성 시 비즈니스 규칙 검증
- **사이드 이펙트 없음**: 순수 함수만 제공

### Entities (엔티티)

- **식별자**: 고유 ID로 구분
- **생명주기**: 상태 변화 관리
- **불변 식별자**: ID는 변경 불가능
- **비즈니스 로직**: 해당 엔티티만의 비즈니스 규칙

### Domain Services (도메인 서비스)

- **무상태**: 상태를 갖지 않는 순수 서비스
- **도메인 로직**: 여러 객체에 걸친 복잡한 비즈니스 로직
- **협력**: Value Objects와 Entities 간의 조율
- **순수성**: 사이드 이펙트 최소화

## 확장 가능성

### 이벤트 기반 아키텍처 준비

각 도메인은 향후 Domain Events 발행이 가능한 구조:

```python
# 향후 확장 예시
class PortfolioRebalancedEvent:
    def __init__(self, portfolio_id: str, old_weights: dict, new_weights: dict):
        self.portfolio_id = portfolio_id
        self.old_weights = old_weights
        self.new_weights = new_weights
        self.timestamp = datetime.utcnow()
```

### CQRS 패턴 준비

읽기/쓰기 분리를 위한 구조적 기반 완성:

```python
# Command 측: 도메인 서비스 활용
class RebalancePortfolioCommand:
    def execute(self, portfolio_service: PortfolioDomainService):
        return portfolio_service.optimize_portfolio(assets)

# Query 측: 읽기 최적화 모델
class PortfolioReadModel:
    def get_optimized_weights(self, portfolio_id: str):
        return cached_optimization_result
```

## 테스트 전략

### 도메인 테스트

각 도메인별로 독립적인 테스트 수행:

```bash
# 백테스트 도메인 테스트
python -c "
from app.domains.backtest.services.backtest_domain_service import BacktestDomainService
from app.domains.backtest.value_objects.date_range import DateRange

service = BacktestDomainService()
date_range = DateRange('2023-01-01', '2023-12-31')
result = service.generate_backtest_result('test', 'AAPL', 'SMA', 0.15, 0.12)
print(f'백테스트 결과 생성 성공: {result.result_id}')
"
```

### 통합 테스트

도메인 간 협력 검증:

```python
# 포트폴리오 최적화 통합 테스트
portfolio_service = PortfolioDomainService()
data_service = DataDomainService()

# 데이터 준비
market_data = data_service.create_market_data("AAPL", historical_prices)

# 포트폴리오 최적화
assets = [create_asset("AAPL", market_data), create_cash_asset()]
optimized = portfolio_service.optimize_portfolio(assets, risk_tolerance=0.6)

assert sum(optimized.values()) == 1.0  # 가중치 합계 검증
```

## 성능 고려사항

### 메모리 효율성

- **Value Objects**: 불변성으로 안전한 공유 가능
- **Lazy Loading**: 필요시에만 복잡한 계산 수행
- **캐싱**: 도메인 서비스 결과 캐싱

### 계산 최적화

- **벡터화**: numpy 기반 대량 데이터 처리
- **병렬화**: 독립적인 도메인 로직 병렬 실행
- **캐시 활용**: 중복 계산 방지

## 마이그레이션 가이드

### 기존 서비스와 통합

현재는 기존 `app/services` 계층과 호환성 유지하며, 점진적 마이그레이션 가능:

```python
# 기존 서비스에서 도메인 서비스 활용
from app.services.backtest_service import BacktestService
from app.domains.portfolio.services.portfolio_domain_service import PortfolioDomainService

class EnhancedBacktestService(BacktestService):
    def __init__(self):
        super().__init__()
        self.portfolio_domain_service = PortfolioDomainService()
    
    async def run_portfolio_optimization(self, assets):
        # 도메인 서비스 활용
        return self.portfolio_domain_service.optimize_portfolio(assets)
```

### Phase 4: 완전 통합

다음 단계에서는 API 엔드포인트가 도메인 서비스를 직접 활용하도록 진화할 예정입니다.
