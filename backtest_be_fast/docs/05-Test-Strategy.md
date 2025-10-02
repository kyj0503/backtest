# FastAPI 백엔드 테스트 전략 가이드

## 목차

1. [테스트 전략 개요](#테스트-전략-개요)
2. [테스트 피라미드](#테스트-피라미드)
3. [테스트 환경 설정](#테스트-환경-설정)
4. [단위 테스트 (Unit Tests)](#단위-테스트-unit-tests)
5. [통합 테스트 (Integration Tests)](#통합-테스트-integration-tests)
6. [E2E 테스트 (End-to-End Tests)](#e2e-테스트-end-to-end-tests)
7. [테스트 작성 가이드라인](#테스트-작성-가이드라인)
8. [테스트 실행 및 CI/CD](#테스트-실행-및-cicd)

---

## 테스트 전략 개요

### 왜 테스트가 필요한가?

#### 자동화된 테스트의 가치
- **빠른 피드백**: 코드 변경 시 즉각적인 검증
- **안정성**: 리팩터링과 기능 추가 시 기존 기능 보장
- **문서화**: 테스트는 살아있는 문서 역할
- **비용 절감**: 버그를 조기에 발견하여 수정 비용 절감

#### 테스트의 핵심 원칙 (FIRST)

1. **Fast (빠르게)**: 테스트는 빠르게 실행되어야 함
2. **Independent (독립적)**: 각 테스트는 독립적으로 실행 가능
3. **Repeatable (반복 가능)**: 어느 환경에서든 동일한 결과
4. **Self-Validating (자가 검증)**: 성공/실패가 명확
5. **Timely (적시에)**: 프로덕션 코드 작성 직전에 작성

---

## 테스트 피라미드

```
      /\
     /E2E\ ← 적은 수 (5-10%)
    /____\     느림, 비용 높음
   /      \
  / 통합    \ ← 중간 수 (20-30%)
 /________\
/          \
/  단위테스트 \ ← 많은 수 (60-75%)
/__________\   빠름, 비용 낮음
```

### 테스트 비율 가이드라인

- **단위 테스트 (60-75%)**: 개별 함수/클래스의 로직 검증
- **통합 테스트 (20-30%)**: 컴포넌트 간 상호작용 검증
- **E2E 테스트 (5-10%)**: 전체 워크플로우 검증

---

## 테스트 환경 설정

### 프로젝트 구조

```
backtest_be_fast/
├── app/
│   ├── api/
│   ├── core/
│   ├── domains/
│   ├── models/
│   ├── repositories/
│   ├── services/
│   └── ...
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # pytest 설정 및 공통 fixtures
│   ├── fixtures/            # 테스트 데이터 팩토리
│   │   ├── __init__.py
│   │   ├── backtest_fixtures.py
│   │   └── portfolio_fixtures.py
│   ├── unit/                # 단위 테스트
│   │   ├── test_services.py
│   │   ├── test_repositories.py
│   │   └── test_domain_logic.py
│   ├── integration/         # 통합 테스트
│   │   ├── test_api_endpoints.py
│   │   └── test_database_integration.py
│   └── e2e/                 # E2E 테스트
│       └── test_backtest_workflow.py
└── pytest.ini               # pytest 설정 파일
```

### pytest 설정 (pytest.ini)

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 비동기 테스트 지원
asyncio_mode = auto

# 마커 정의
markers =
    unit: Unit tests (단위 테스트)
    integration: Integration tests (통합 테스트)
    e2e: End-to-end tests (E2E 테스트)
    slow: Slow running tests (느린 테스트)
    db: Tests that require database (DB 필요)

# 출력 설정
addopts = 
    -ra
    --strict-markers
    --strict-config
    --showlocals
    -v

# 커버리지 설정
[coverage:run]
source = app
omit = 
    */tests/*
    */test_*.py
    */__pycache__/*
    */site-packages/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False
```

---

## 단위 테스트 (Unit Tests)

### 단위 테스트의 특징

- **격리된 환경**: 외부 의존성 없이 독립적으로 실행
- **빠른 실행**: 밀리초 단위로 실행
- **단일 책임**: 하나의 기능만 테스트
- **Mock 사용**: 외부 의존성은 Mock으로 대체

### Given-When-Then 패턴

```python
def test_example():
    # Given: 테스트를 위한 준비 단계
    input_data = {"symbol": "AAPL", "amount": 10000}
    
    # When: 실제 테스트할 동작 실행
    result = some_function(input_data)
    
    # Then: 결과 검증
    assert result.success is True
    assert result.data is not None
```

### 도메인 로직 테스트 예시

```python
import pytest
from decimal import Decimal
from app.domains.portfolio.entities import Portfolio, Position

class TestPortfolioDomainLogic:
    """포트폴리오 도메인 로직 단위 테스트"""
    
    def test_포트폴리오_초기_자본금_계산(self):
        # Given
        initial_cash = Decimal("10000.00")
        portfolio = Portfolio(initial_cash=initial_cash)
        
        # When
        total_value = portfolio.get_total_value()
        
        # Then
        assert total_value == initial_cash
        assert portfolio.cash == initial_cash
        assert len(portfolio.positions) == 0
    
    def test_포지션_추가_시_현금_감소(self):
        # Given
        portfolio = Portfolio(initial_cash=Decimal("10000.00"))
        symbol = "AAPL"
        quantity = 10
        price = Decimal("150.00")
        
        # When
        portfolio.add_position(symbol, quantity, price)
        
        # Then
        expected_cash = Decimal("10000.00") - (quantity * price)
        assert portfolio.cash == expected_cash
        assert len(portfolio.positions) == 1
        assert portfolio.positions[symbol].quantity == quantity
    
    def test_포트폴리오_총_가치_계산(self):
        # Given
        portfolio = Portfolio(initial_cash=Decimal("10000.00"))
        portfolio.add_position("AAPL", 10, Decimal("150.00"))
        portfolio.add_position("GOOGL", 5, Decimal("280.00"))
        
        # When
        current_prices = {"AAPL": Decimal("155.00"), "GOOGL": Decimal("290.00")}
        total_value = portfolio.calculate_total_value(current_prices)
        
        # Then
        # Cash: 10000 - (10*150 + 5*280) = 10000 - 2900 = 7100
        # AAPL: 10 * 155 = 1550
        # GOOGL: 5 * 290 = 1450
        # Total: 7100 + 1550 + 1450 = 10100
        assert total_value == Decimal("10100.00")
```

### 서비스 레이어 테스트 (Mock 사용)

```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.services.backtest_service import BacktestService
from app.models.requests import BacktestRequest

class TestBacktestService:
    """백테스트 서비스 단위 테스트"""
    
    @pytest.fixture
    def mock_data_repository(self):
        """데이터 리포지토리 Mock"""
        repo = Mock()
        repo.get_price_data = AsyncMock(return_value=[
            {"date": "2023-01-01", "close": 150.0},
            {"date": "2023-01-02", "close": 155.0},
        ])
        return repo
    
    @pytest.fixture
    def backtest_service(self, mock_data_repository):
        """백테스트 서비스 인스턴스"""
        return BacktestService(data_repository=mock_data_repository)
    
    @pytest.mark.asyncio
    async def test_백테스트_실행_성공(self, backtest_service, mock_data_repository):
        # Given
        request = BacktestRequest(
            symbol="AAPL",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=10000.0,
            strategy="buy_and_hold"
        )
        
        # When
        result = await backtest_service.run_backtest(request)
        
        # Then
        assert result.success is True
        assert result.metrics is not None
        mock_data_repository.get_price_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_잘못된_심볼로_백테스트_실패(self, backtest_service, mock_data_repository):
        # Given
        mock_data_repository.get_price_data = AsyncMock(return_value=[])
        request = BacktestRequest(
            symbol="INVALID",
            start_date="2023-01-01",
            end_date="2023-12-31",
            initial_capital=10000.0,
            strategy="buy_and_hold"
        )
        
        # When/Then
        with pytest.raises(ValueError, match="No data available"):
            await backtest_service.run_backtest(request)
```

---

## 통합 테스트 (Integration Tests)

### 통합 테스트의 특징

- **실제 의존성 사용**: DB, 외부 API 등 실제 컴포넌트와 통합
- **트랜잭션 롤백**: 테스트 후 DB 상태 원복
- **테스트 데이터베이스**: 별도의 테스트용 DB 사용

### API 엔드포인트 통합 테스트

```python
import pytest
from httpx import AsyncClient
from app.main import app
from tests.fixtures.backtest_fixtures import create_backtest_request_data

@pytest.mark.integration
class TestBacktestAPI:
    """백테스트 API 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_백테스트_실행_API_성공(self, client: AsyncClient):
        # Given
        request_data = create_backtest_request_data(
            symbol="AAPL",
            initial_capital=10000.0
        )
        
        # When
        response = await client.post("/api/v1/backtest/run", json=request_data)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "metrics" in data["data"]
        assert "equity_curve" in data["data"]
    
    @pytest.mark.asyncio
    async def test_백테스트_히스토리_조회(self, client: AsyncClient, db_session):
        # Given: DB에 백테스트 기록 생성
        from tests.fixtures.backtest_fixtures import create_backtest_history
        history = create_backtest_history(db_session, user_id=1)
        db_session.commit()
        
        # When
        response = await client.get(f"/api/v1/backtest/history?user_id=1")
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        assert data["data"][0]["symbol"] == history.symbol
    
    @pytest.mark.asyncio
    async def test_잘못된_요청_데이터로_400_에러(self, client: AsyncClient):
        # Given
        invalid_request = {
            "symbol": "",  # 빈 심볼
            "initial_capital": -1000  # 음수 자본금
        }
        
        # When
        response = await client.post("/api/v1/backtest/run", json=invalid_request)
        
        # Then
        assert response.status_code == 422  # Validation error
```

### 데이터베이스 통합 테스트

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.backtest_history_repository import BacktestHistoryRepository
from app.models.schemas import BacktestHistory

@pytest.mark.integration
@pytest.mark.db
class TestBacktestHistoryRepository:
    """백테스트 히스토리 리포지토리 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_백테스트_결과_저장(self, db_session: AsyncSession):
        # Given
        repository = BacktestHistoryRepository(db_session)
        history_data = {
            "user_id": 1,
            "symbol": "AAPL",
            "strategy": "buy_and_hold",
            "initial_capital": 10000.0,
            "final_value": 12500.0,
            "total_return": 0.25
        }
        
        # When
        saved_history = await repository.save(history_data)
        await db_session.commit()
        
        # Then
        assert saved_history.id is not None
        retrieved = await repository.get_by_id(saved_history.id)
        assert retrieved.symbol == "AAPL"
        assert retrieved.total_return == 0.25
    
    @pytest.mark.asyncio
    async def test_사용자별_히스토리_조회(self, db_session: AsyncSession):
        # Given
        repository = BacktestHistoryRepository(db_session)
        user_id = 1
        
        # 여러 백테스트 기록 생성
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            await repository.save({
                "user_id": user_id,
                "symbol": symbol,
                "strategy": "buy_and_hold",
                "initial_capital": 10000.0
            })
        await db_session.commit()
        
        # When
        histories = await repository.get_by_user_id(user_id)
        
        # Then
        assert len(histories) == 3
        symbols = [h.symbol for h in histories]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols
        assert "MSFT" in symbols
```

---

## E2E 테스트 (End-to-End Tests)

### E2E 테스트의 특징

- **실제 시나리오**: 사용자의 전체 워크플로우 테스트
- **모든 레이어 포함**: API → Service → Repository → DB
- **느린 실행**: 가장 많은 시간 소요
- **적은 수**: 핵심 시나리오만 테스트

### 전체 백테스트 워크플로우 테스트

```python
import pytest
from httpx import AsyncClient
from decimal import Decimal

@pytest.mark.e2e
@pytest.mark.slow
class TestBacktestWorkflow:
    """백테스트 전체 워크플로우 E2E 테스트"""
    
    @pytest.mark.asyncio
    async def test_백테스트_전체_워크플로우(self, client: AsyncClient):
        """
        시나리오:
        1. 사용 가능한 전략 목록 조회
        2. 백테스트 실행
        3. 실행 결과 조회
        4. 히스토리에 저장 확인
        """
        
        # 1. Given: 사용 가능한 전략 목록 조회
        strategies_response = await client.get("/api/v1/backtest/strategies")
        assert strategies_response.status_code == 200
        strategies = strategies_response.json()["data"]
        assert len(strategies) > 0
        
        strategy_name = strategies[0]["name"]
        
        # 2. When: 백테스트 실행
        backtest_request = {
            "symbol": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 10000.0,
            "strategy": strategy_name,
            "parameters": {}
        }
        
        backtest_response = await client.post(
            "/api/v1/backtest/run",
            json=backtest_request
        )
        
        # 3. Then: 백테스트 결과 검증
        assert backtest_response.status_code == 200
        backtest_data = backtest_response.json()["data"]
        
        assert "metrics" in backtest_data
        assert "total_return" in backtest_data["metrics"]
        assert "sharpe_ratio" in backtest_data["metrics"]
        assert "max_drawdown" in backtest_data["metrics"]
        
        assert "equity_curve" in backtest_data
        assert len(backtest_data["equity_curve"]) > 0
        
        assert "trades" in backtest_data
        
        # 4. 히스토리 저장 확인
        history_response = await client.get(
            f"/api/v1/backtest/history?user_id=1&limit=1"
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()["data"]
        assert len(history_data) > 0
        assert history_data[0]["symbol"] == "AAPL"
        assert history_data[0]["strategy"] == strategy_name
```

---

## 테스트 작성 가이드라인

### 1. 테스트 명명 규칙

```python
# ❌ 나쁜 예
def test_1():
    pass

def test_function():
    pass

# ✅ 좋은 예
def test_포트폴리오_초기화_시_현금이_설정됨():
    pass

def test_잘못된_심볼로_백테스트_실행_시_예외_발생():
    pass

def test_calculate_returns_with_valid_data():
    pass
```

### 2. Fixture 활용

```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def db_session():
    """테스트용 DB 세션"""
    engine = create_async_engine(
        "mysql+asyncmy://test:test@localhost/test_db",
        echo=False
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()  # 테스트 후 롤백

@pytest.fixture
async def client():
    """테스트용 HTTP 클라이언트"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### 3. Factory Pattern for Test Data

```python
# tests/fixtures/backtest_fixtures.py
from datetime import datetime, timedelta
from decimal import Decimal
import factory
from faker import Faker

fake = Faker()

class BacktestRequestFactory(factory.Factory):
    """백테스트 요청 데이터 팩토리"""
    class Meta:
        model = dict
    
    symbol = factory.Faker('random_element', elements=['AAPL', 'GOOGL', 'MSFT'])
    start_date = factory.LazyFunction(
        lambda: (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    )
    end_date = factory.LazyFunction(
        lambda: datetime.now().strftime("%Y-%m-%d")
    )
    initial_capital = factory.Faker('pydecimal', left_digits=5, right_digits=2, positive=True)
    strategy = "buy_and_hold"
    parameters = {}

# 사용 예시
def test_example():
    request_data = BacktestRequestFactory()
    # 특정 값 오버라이드
    request_data_custom = BacktestRequestFactory(symbol="TSLA", initial_capital=50000)
```

### 4. 파라미터라이즈 테스트

```python
@pytest.mark.parametrize("symbol,expected", [
    ("AAPL", True),
    ("GOOGL", True),
    ("INVALID", False),
    ("", False),
])
def test_심볼_유효성_검증(symbol, expected):
    # Given
    validator = SymbolValidator()
    
    # When
    result = validator.is_valid(symbol)
    
    # Then
    assert result == expected
```

### 5. 비동기 테스트 작성

```python
@pytest.mark.asyncio
async def test_비동기_백테스트_실행():
    # Given
    service = BacktestService()
    
    # When
    result = await service.run_backtest_async(request)
    
    # Then
    assert result.success is True
```

### 6. 예외 테스트

```python
def test_음수_자본금으로_예외_발생():
    # Given
    invalid_capital = -1000.0
    
    # When/Then
    with pytest.raises(ValueError, match="Capital must be positive"):
        Portfolio(initial_cash=invalid_capital)
```

### 7. Mock과 Stub 사용

```python
from unittest.mock import Mock, patch, AsyncMock

def test_외부_API_호출_Mock():
    # Given
    mock_api_client = Mock()
    mock_api_client.get_price_data.return_value = [{"price": 150.0}]
    
    service = BacktestService(api_client=mock_api_client)
    
    # When
    result = service.fetch_data("AAPL")
    
    # Then
    assert len(result) == 1
    mock_api_client.get_price_data.assert_called_once_with("AAPL")

@patch('app.services.yfinance_service.yf.download')
def test_yfinance_다운로드_Patch(mock_download):
    # Given
    mock_download.return_value = pd.DataFrame({"Close": [150.0, 155.0]})
    
    # When
    result = fetch_stock_data("AAPL")
    
    # Then
    assert len(result) == 2
```

---

## 테스트 실행 및 CI/CD

### 로컬 실행

```bash
# 모든 테스트 실행
pytest

# 특정 마커 테스트만 실행
pytest -m unit
pytest -m integration
pytest -m "not slow"

# 특정 파일 테스트
pytest tests/unit/test_services.py

# 특정 테스트 함수
pytest tests/unit/test_services.py::TestBacktestService::test_백테스트_실행_성공

# 커버리지 포함
pytest --cov=app --cov-report=html

# 병렬 실행 (pytest-xdist)
pytest -n auto

# 실패한 테스트만 재실행
pytest --lf

# 상세 출력
pytest -vv
```

### Docker에서 테스트 실행

```bash
# Docker Compose로 테스트 환경 구성
docker compose -f compose/compose.dev.yaml up -d mysql redis

# 테스트 실행
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast pytest

# 특정 마커 테스트
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast pytest -m unit

# 커버리지 포함
docker compose -f compose/compose.dev.yaml run --rm backtest_be_fast pytest --cov=app
```

### CI/CD 파이프라인 (GitHub Actions)

```yaml
name: Backend Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test_password
          MYSQL_DATABASE: test_db
        ports:
          - 3306:3306
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3
      
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backtest_be_fast
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run Unit Tests
      run: |
        cd backtest_be_fast
        pytest tests/unit -v --cov=app --cov-report=xml
    
    - name: Run Integration Tests
      env:
        DATABASE_URL: mysql+asyncmy://root:test_password@localhost:3306/test_db
        REDIS_URL: redis://localhost:6379
      run: |
        cd backtest_be_fast
        pytest tests/integration -v
    
    - name: Upload Coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./backtest_be_fast/coverage.xml
```

---

## 구현 현황 및 개선 계획

### 현재 상태 (구현 예정)

```
테스트 파일:  0개
테스트:       0개
커버리지:     0%
```

### 단기 계획 (1-2주)
- [ ] 테스트 인프라 구축 (pytest, fixtures, conftest)
- [ ] 도메인 로직 단위 테스트 작성 (포트폴리오, 전략)
- [ ] 서비스 레이어 단위 테스트 (Mock 사용)
- [ ] API 엔드포인트 통합 테스트
- [ ] 목표: 60% 이상 커버리지

### 중기 계획 (1개월)
- [ ] 리포지토리 통합 테스트 (실제 DB)
- [ ] E2E 테스트 작성 (핵심 워크플로우)
- [ ] CI/CD 파이프라인 통합
- [ ] 목표: 80% 이상 커버리지

### 장기 계획 (3개월+)
- [ ] 성능 테스트 (부하 테스트, 스트레스 테스트)
- [ ] 보안 테스트
- [ ] 테스트 메트릭 모니터링
- [ ] 자동화된 리그레션 테스트

---

## 참고 자료

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)
- [Effective Python Testing With Pytest](https://realpython.com/pytest-python-testing/)

---

**작성일**: 2025-02-10  
**최종 업데이트**: 2025-02-10  
**버전**: 1.0.0  
**작성자**: Backtest Team
