# 백테스팅 플랫폼 테스트 코드 작성 가이드

## 서론

소프트웨어 프로젝트에서 테스트는 오류를 사전에 발견하고 품질을 높이는 중요한 도구다. 
특히 금융 데이터를 다루는 백테스팅 플랫폼에서는 계산 로직의 정확성과 데이터 무결성이 매우 중요하기 때문에 체계적인 테스트 전략이 필수적이다.

이 문서는 React/TypeScript 프론트엔드와 FastAPI 백엔드로 구성된 백테스팅 플랫폼 개발 시 적용할 수 있는 **실용적인** 테스트 전략을 정리한다.
대학 졸업 작품으로서 모든 코드를 테스트하는 것은 비현실적이므로, **가치가 높은 20%의 핵심 기능에 집중하여 80%의 신뢰성을 확보**하는 것을 목표로 한다[2].

### 이 문서의 핵심 원칙

1. **과도한 테스트 지양**: 단순 getter/setter, 프레임워크 내부 동작은 테스트하지 않는다
2. **가치 중심**: 백테스팅 계산 로직, 데이터 처리, API 계약 등 핵심 기능에 집중
3. **실용성**: 졸업 작품 일정 내에서 실현 가능한 범위의 테스트 작성
4. **유지보수성**: 코드 변경 시 쉽게 수정 가능하도록 구현에 강결합되지 않게 작성
## 테스트 유형과 우선순위

### 1. 단위 테스트 (Unit Test)

**정의**: 개별 함수나 메서드의 동작을 독립적으로 검증하는 테스트

**특징**:
- 외부 의존성(DB, API)을 Mock/Stub으로 대체하여 격리
- 실행 속도가 빠르고(ms 단위) 피드백이 즉각적
- 재현성이 높아 안정적으로 실행 가능

**백테스팅 프로젝트에서의 활용 예시**:
- 전략 클래스의 계산 로직 (예: RSI 계산, 볼린저 밴드 상/하단 계산)
- 데이터 변환 함수 (예: pandas Timedelta 변환, JSON 직렬화)
- 유틸리티 함수 (예: 날짜 포맷팅, 수익률 계산)

```python
# 예시: RSI 전략의 시그널 생성 로직 테스트
def test_rsi_strategy_generates_buy_signal_when_oversold():
    # given: RSI가 30 이하일 때
    strategy = RsiStrategy(period=14, oversold=30)
    mock_data = create_mock_ohlcv_with_rsi(rsi_value=25)
    
    # when: 시그널 생성
    signal = strategy.generate_signal(mock_data)
    
    # then: 매수 시그널 발생
    assert signal == "BUY"
```

### 2. 통합 테스트 (Integration Test)

**정의**: 여러 모듈이나 계층 간 상호작용을 검증하는 테스트

**특징**:
- 실제 데이터베이스, 외부 API 등과 통합하여 테스트
- 단위 테스트보다 느리지만(초 단위) 시스템의 실제 동작 검증
- 모듈 간 인터페이스와 데이터 흐름 확인

**백테스팅 프로젝트에서의 활용 예시**:
- API 엔드포인트와 서비스 계층 통합 (FastAPI TestClient 활용)
- 데이터베이스 조회 및 저장 (실제 테스트 DB 사용)
- 외부 API 연동 (yfinance, Naver Search API → Fake/Mock 활용)

```python
# 예시: 백테스트 실행 통합 테스트
def test_backtest_endpoint_returns_valid_result(test_client, test_db):
    # given: 유효한 백테스트 요청
    request_data = {
        "strategy": "sma_crossover",
        "ticker": "005930.KS",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    
    # when: API 호출
    response = test_client.post("/api/v1/backtest", json=request_data)
    
    # then: 정상 응답과 결과 검증
    assert response.status_code == 200
    result = response.json()
    assert "total_return" in result
    assert "sharpe_ratio" in result
```

### 3. E2E 테스트 (End-to-End Test)

**정의**: 사용자 관점에서 전체 시스템의 워크플로를 검증하는 테스트

**특징**:
- 브라우저 자동화 도구 활용 (Playwright, Cypress)
- 가장 느리지만(분 단위) 사용자 경험 전체를 검증
- 프론트엔드 + 백엔드 + DB + 외부 서비스 모두 포함

**백테스팅 프로젝트에서의 활용 (선택적)**:
- 핵심 사용자 시나리오 1~2개만 작성 권장
- 예: "전략 선택 → 파라미터 입력 → 백테스트 실행 → 결과 차트 확인"

> **졸업 작품에서의 우선순위**: 단위 테스트 > 통합 테스트 > E2E 테스트  
> E2E는 시간이 부족하면 생략 가능하며, 핵심 로직은 단위/통합 테스트로 충분히 커버
## 좋은 테스트의 FIRST 원칙

### Fast (빠른 실행)
테스트는 빠르게 실행되어 개발자가 수시로 실행할 수 있어야 한다.
- **단위 테스트**: 수백 개가 1초 이내 실행
- **통합 테스트**: 수십 개가 10초 이내 실행
- 느린 테스트는 개발자가 실행을 꺼리게 되어 테스트의 가치가 떨어짐

### Independent (독립적)
각 테스트는 서로 독립적이며 실행 순서에 무관하게 통과해야 한다.
- 테스트 간 공유 상태 사용 금지
- DB 상태는 각 테스트 전/후에 초기화
- 한 테스트의 실패가 다른 테스트에 영향을 주면 안 됨

### Repeatable (반복 가능)
어느 환경(로컬, CI, 팀원 PC)에서도 일관된 결과를 보여야 한다.
- 외부 API는 Mock/Fake로 대체하여 네트워크 의존성 제거
- 현재 시간에 의존하는 로직은 시간을 주입받도록 설계
- 랜덤 값은 시드를 고정하거나 테스트에서 통제

### Self-Validating (자가 검증)
테스트 결과는 성공/실패가 명확해야 하며, 사람이 로그를 확인할 필요가 없어야 한다.
- `assert`, `expect` 등 명시적인 검증문 사용
- 콘솔 출력을 보고 수동으로 확인하는 테스트는 피할 것

### Timely (적시 작성)
테스트는 프로덕션 코드 작성 직후 또는 직전(TDD)에 작성한다.
- 코드 완성 후 한참 뒤에 테스트를 작성하면 누락이 생김
- 리팩터링 시 테스트가 안전망 역할을 하므로 먼저 작성 권장

---

## 테스트 작성 패턴: Given-When-Then

테스트는 **3단계 구조**로 작성하면 가독성이 높아진다:

```python
def test_portfolio_calculates_total_return_correctly():
    # Given (준비): 초기 상태 설정
    portfolio = Portfolio(initial_cash=10_000_000)
    portfolio.buy("005930.KS", quantity=100, price=70_000)
    
    # When (실행): 테스트할 동작 수행
    portfolio.update_price("005930.KS", current_price=75_000)
    total_return = portfolio.calculate_total_return()
    
    # Then (검증): 기대 결과 확인
    assert total_return == 0.05  # 5% 수익
```

```typescript
// React 컴포넌트 테스트 예시
describe('BacktestForm', () => {
  it('should submit backtest when all required fields are filled', async () => {
    // Given: 폼 렌더링
    render(<BacktestForm />);
    
    // When: 사용자가 입력하고 제출
    await userEvent.selectOptions(screen.getByLabelText('전략'), 'SMA Crossover');
    await userEvent.type(screen.getByLabelText('티커'), '005930.KS');
    await userEvent.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // Then: API 호출 확인
    expect(mockApiCall).toHaveBeenCalledWith(
      expect.objectContaining({ strategy: 'SMA Crossover' })
    );
  });
});
```

### 테스트 이름 작성 규칙 (USE 전략)

**U**nit (테스트 대상) + **S**cenario (시나리오) + **E**xpectation (기대 결과)

- ✅ `test_rsi_strategy_generates_buy_signal_when_rsi_below_30`
- ✅ `test_portfolio_raises_error_when_insufficient_cash`
- ❌ `test_strategy` (무엇을 테스트하는지 불명확)
- ❌ `test_case_1` (시나리오와 기대 결과 없음)
## 가치 기반 테스트 전략: 20%로 80% 커버하기

> **핵심 원칙**: 모든 코드를 테스트하려는 것은 비효율적이다.  
> 가치가 높은 20% 핵심 기능에 집중하여 시스템 신뢰도 80%를 확보한다 [2]

### 백테스팅 프로젝트에서 **반드시 테스트해야 할 것**

#### 1. 도메인 정책 테스트 (단위 테스트)
핵심 비즈니스 로직과 계산 정확성을 검증한다.

**테스트 대상**:
- ✅ 전략 클래스의 시그널 생성 로직 (RSI, MACD, 볼린저 밴드 등)
- ✅ 수익률 계산, Sharpe Ratio, MDD 등 성과 지표 계산
- ✅ 주문 실행 로직 (매수/매도 수량, 수수료 계산)
- ✅ pandas Timedelta 변환 로직 (backtesting.py 호환성)

```python
# 예시: 볼린저 밴드 계산 로직 테스트
def test_bollinger_bands_calculates_correct_upper_band():
    # Given: 평균 100, 표준편차 10, K=2
    prices = pd.Series([100, 100, 100, 100, 100])
    
    # When: 볼린저 밴드 계산
    upper, middle, lower = calculate_bollinger_bands(prices, period=5, k=2)
    
    # Then: 상단 밴드 = 평균 + (2 * 표준편차)
    assert upper.iloc[-1] == 100 + (2 * 10)  # 120
```

#### 2. 유스케이스 테스트 (통합 테스트)
사용자의 실제 워크플로가 올바르게 동작하는지 검증한다.

**테스트 대상**:
- ✅ 백테스트 실행 API (전략 선택 → 데이터 조회 → 계산 → 결과 반환)
- ✅ 데이터 수집 및 캐싱 (yfinance → DB 저장 → 조회)
- ✅ 뉴스 검색 API (Naver Search → 파싱 → 응답)

```python
def test_execute_backtest_with_sma_strategy(test_client, test_db):
    # Given: 유효한 백테스트 요청
    request = {
        "strategy": "sma_crossover",
        "ticker": "005930.KS",
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "parameters": {"short_window": 50, "long_window": 200}
    }
    
    # When: 백테스트 실행
    response = test_client.post("/api/v1/backtest", json=request)
    
    # Then: 성공 응답과 필수 필드 검증
    assert response.status_code == 200
    result = response.json()
    assert "total_return" in result
    assert "sharpe_ratio" in result
    assert result["sharpe_ratio"] >= -3  # 합리적 범위 확인
```

#### 3. 직렬화/역직렬화 테스트
데이터 변환과 API 계약이 올바른지 검증한다.

**테스트 대상**:
- ✅ Pydantic 모델 직렬화 (Request/Response DTO)
- ✅ JSON 직렬화 (차트 데이터, 백테스트 결과)
- ✅ DataFrame ↔ JSON 변환

### 백테스팅 프로젝트에서 **테스트하지 않아도 되는 것**

- ❌ 단순 getter/setter (예: `get_ticker()`, `set_strategy()`)
- ❌ 프레임워크 내부 동작 (FastAPI 라우팅, React 렌더링)
- ❌ 외부 라이브러리 검증 (pandas의 `rolling()`, yfinance의 `download()`)
- ❌ 단순 UI 레이아웃 (버튼 위치, 색상 등)
- ❌ 로깅, 디버그 출력

---

## 테스트 더블: Mock vs Stub vs Fake

외부 의존성을 제거하여 테스트를 독립적으로 만들기 위해 **테스트 더블**을 사용한다.

### 1. Dummy (더미)
테스트에 전달되지만 실제로 사용되지 않는 객체.

```python
def test_save_backtest_result(result_repository):
    # 로거는 실제로 사용되지 않으므로 None으로 전달
    service = BacktestService(repository=result_repository, logger=None)
```

### 2. Stub (스텁)
미리 정의된 응답을 반환하는 객체.

```python
class StubYFinanceDataRepository:
    def fetch_ohlcv(self, ticker, start_date, end_date):
        # 항상 고정된 테스트 데이터 반환
        return pd.DataFrame({
            'Open': [70000, 71000],
            'High': [72000, 73000],
            'Low': [69000, 70000],
            'Close': [71000, 72000],
            'Volume': [1000000, 1100000]
        })
```

### 3. Spy (스파이)
실제 객체를 감싸서 호출 기록을 추적하는 객체.

```python
def test_backtest_service_calls_repository(mocker):
    # repository의 save 메서드 호출 감시
    spy = mocker.spy(result_repository, 'save')
    
    service.execute_backtest(request)
    
    # save가 1번 호출되었는지 확인
    assert spy.call_count == 1
```

### 4. Mock (목)
기대되는 호출을 검증하는 객체.

```python
def test_news_service_calls_naver_api(mocker):
    # Naver API 호출을 Mock으로 대체
    mock_api = mocker.patch('app.services.naver_api.search')
    mock_api.return_value = {'items': [...]}
    
    news_service.search_news('삼성전자')
    
    # 특정 파라미터로 호출되었는지 검증
    mock_api.assert_called_once_with(query='삼성전자', display=10)
```

### 5. Fake (페이크)
실제 구현과 유사하지만 간소화된 버전.

```python
class FakeDatabaseRepository:
    """인메모리로 동작하는 가짜 DB"""
    def __init__(self):
        self.storage = {}
    
    def save(self, key, value):
        self.storage[key] = value
    
    def find_by_id(self, key):
        return self.storage.get(key)
```

### 백테스팅 프로젝트에서의 활용 지침

| 상황 | 권장 테스트 더블 |
|------|----------------|
| yfinance API 호출 | Fake (미리 준비한 CSV 데이터 사용) |
| Naver Search API | Mock (네트워크 의존성 제거) |
| 데이터베이스 조회 | 실제 테스트 DB 사용 (SQLite/H2) |
| 알림 발송 | Dummy (실제 발송 안 함) |
| backtesting.py 엔진 | 실제 객체 사용 (계산 검증 필요) |

> **원칙**: 가능한 한 **실제 객체**를 사용하고, 불가피한 경우에만 테스트 더블 사용 [8]  
> 이유: Mock을 많이 사용하면 구현에 강결합되어 리팩터링 시 테스트가 쉽게 깨짐

---

## 과도한 테스트의 위험 (Overspecification)

### 과도한 테스트란?

1. **구현 세부사항 검증**: 내부 메서드 호출 순서, private 변수 상태 등
2. **지나치게 많은 Mock 사용**: 10개 이상의 Mock 객체를 설정
3. **변경에 취약한 테스트**: 코드 리팩터링 시 테스트가 쉽게 깨짐

### 나쁜 예시 (과도한 명세)

```python
def test_backtest_service_internal_implementation():  # ❌ 나쁜 예
    service = BacktestService()
    spy_calculate = mocker.spy(service, '_calculate_signals')
    spy_execute = mocker.spy(service, '_execute_orders')
    spy_save = mocker.spy(service, '_save_result')
    
    service.run_backtest(request)
    
    # 내부 메서드 호출 순서까지 검증 → 리팩터링 불가능
    assert spy_calculate.call_count == 1
    assert spy_execute.call_count == 1
    assert spy_save.call_count == 1
```

### 좋은 예시 (행동 중심 검증)

```python
def test_backtest_service_returns_correct_result():  # ✅ 좋은 예
    service = BacktestService()
    
    result = service.run_backtest(request)
    
    # 결과만 검증, 내부 구현은 신경 쓰지 않음
    assert result.total_return > 0
    assert result.sharpe_ratio is not None
```
---

## FastAPI 백엔드 테스트 전략

### 테스트 구조 및 도구

**테스트 프레임워크**: pytest  
**주요 도구**:
- `TestClient`: FastAPI 엔드포인트 테스트 (동기/비동기 모두 지원)
- `pytest-asyncio`: 비동기 함수 테스트
- `pytest-mock`: Mock/Spy 객체 생성
- SQLAlchemy + SQLite: 테스트용 인메모리 DB

**테스트 파일 구조**:
```
backtest_be_fast/
├── tests/
│   ├── conftest.py              # 공통 fixture 정의
│   ├── unit/                    # 단위 테스트
│   │   ├── test_strategies.py  # 전략 로직 테스트
│   │   ├── test_utils.py       # 유틸리티 함수 테스트
│   │   └── test_services.py    # 서비스 로직 테스트
│   ├── integration/             # 통합 테스트
│   │   ├── test_backtest_api.py
│   │   ├── test_data_repository.py
│   │   └── test_yfinance_integration.py
│   └── e2e/                     # E2E 테스트 (선택)
│       └── test_full_workflow.py
```

### 1. 단위 테스트: 전략 로직 검증

```python
# tests/unit/test_rsi_strategy.py
import pytest
from app.strategies.rsi_strategy import RsiStrategy

class TestRsiStrategy:
    """RSI 전략 로직 단위 테스트"""
    
    def test_should_buy_when_rsi_below_oversold(self):
        # Given: RSI가 과매도 구간(30) 이하
        strategy = RsiStrategy(period=14, oversold=30, overbought=70)
        mock_data = create_mock_df_with_rsi(rsi_value=25)
        
        # When: 시그널 생성
        signal = strategy.generate_signal(mock_data)
        
        # Then: 매수 시그널
        assert signal == "BUY"
    
    def test_should_sell_when_rsi_above_overbought(self):
        # Given: RSI가 과매수 구간(70) 이상
        strategy = RsiStrategy(period=14, oversold=30, overbought=70)
        mock_data = create_mock_df_with_rsi(rsi_value=75)
        
        # When: 시그널 생성
        signal = strategy.generate_signal(mock_data)
        
        # Then: 매도 시그널
        assert signal == "SELL"
    
    def test_raises_error_when_invalid_period(self):
        # Given: 잘못된 기간 설정 (음수)
        # When & Then: ValueError 발생
        with pytest.raises(ValueError, match="period must be positive"):
            RsiStrategy(period=-1)
```

### 2. 통합 테스트: API 엔드포인트 검증

```python
# tests/integration/test_backtest_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestBacktestAPI:
    """백테스트 API 통합 테스트"""
    
    def test_execute_backtest_returns_success(self, test_db):
        # Given: 유효한 백테스트 요청
        request_data = {
            "strategy": "sma_crossover",
            "ticker": "005930.KS",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "parameters": {
                "short_window": 50,
                "long_window": 200
            }
        }
        
        # When: POST /api/v1/backtest 호출
        response = client.post("/api/v1/backtest", json=request_data)
        
        # Then: 200 응답과 필수 필드 포함
        assert response.status_code == 200
        result = response.json()
        
        assert "total_return" in result
        assert "sharpe_ratio" in result
        assert "max_drawdown" in result
        assert isinstance(result["total_return"], float)
    
    def test_returns_400_when_invalid_ticker(self):
        # Given: 존재하지 않는 티커
        request_data = {
            "strategy": "sma_crossover",
            "ticker": "INVALID_TICKER",
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        }
        
        # When: API 호출
        response = client.post("/api/v1/backtest", json=request_data)
        
        # Then: 400 Bad Request
        assert response.status_code == 400
        assert "error" in response.json()
```

### 3. Fixture를 활용한 공통 설정

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

@pytest.fixture(scope="function")
def test_db():
    """각 테스트마다 새로운 인메모리 DB 생성"""
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(bind=engine)
    
    # 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def mock_yfinance_data():
    """yfinance 데이터를 Mock으로 대체"""
    return pd.DataFrame({
        'Date': pd.date_range('2023-01-01', periods=100),
        'Open': [70000] * 100,
        'High': [72000] * 100,
        'Low': [69000] * 100,
        'Close': [71000] * 100,
        'Volume': [1000000] * 100
    })
```

### 4. 비동기 함수 테스트

```python
# tests/integration/test_async_services.py
import pytest

@pytest.mark.asyncio
async def test_async_fetch_data_from_yfinance():
    # Given: 비동기 데이터 서비스
    service = AsyncDataService()
    
    # When: 비동기 데이터 조회
    data = await service.fetch_ohlcv("005930.KS", "2023-01-01", "2023-12-31")
    
    # Then: 데이터 반환 확인
    assert not data.empty
    assert "Close" in data.columns
```

### 5. 의존성 오버라이드 (Dependency Override)

```python
# tests/integration/test_with_dependency_override.py
from app.main import app
from app.core.dependencies import get_db

def override_get_db():
    """테스트용 DB로 오버라이드"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def test_with_test_database():
    response = client.get("/api/v1/strategies")
    assert response.status_code == 200
```

---

## React 프론트엔드 테스트 전략

### 테스트 구조 및 도구

**테스트 프레임워크**: Vitest (Jest 호환)  
**주요 도구**:
- `@testing-library/react`: React 컴포넌트 테스트
- `@testing-library/user-event`: 사용자 인터랙션 시뮬레이션
- `msw` (Mock Service Worker): API 요청 모킹

**테스트 파일 구조**:
```
backtest_fe/src/
├── features/
│   └── backtest/
│       ├── components/
│       │   ├── BacktestForm.tsx
│       │   └── BacktestForm.test.tsx       # 컴포넌트 테스트
│       ├── hooks/
│       │   ├── useBacktestForm.ts
│       │   └── useBacktestForm.test.ts     # 커스텀 훅 테스트
│       └── api/
│           ├── backtestApi.ts
│           └── backtestApi.test.ts         # API 클라이언트 테스트
└── test/
    ├── setup.ts                             # 테스트 환경 설정
    └── mocks/
        └── handlers.ts                      # MSW 핸들러
```

### 1. 컴포넌트 단위 테스트

```typescript
// features/backtest/components/BacktestForm.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BacktestForm } from './BacktestForm';

describe('BacktestForm', () => {
  it('should render all required form fields', () => {
    // Given: 폼 렌더링
    render(<BacktestForm />);
    
    // Then: 모든 필수 필드 존재 확인
    expect(screen.getByLabelText('전략 선택')).toBeInTheDocument();
    expect(screen.getByLabelText('티커')).toBeInTheDocument();
    expect(screen.getByLabelText('시작일')).toBeInTheDocument();
    expect(screen.getByLabelText('종료일')).toBeInTheDocument();
  });
  
  it('should submit backtest when form is valid', async () => {
    // Given: 폼 렌더링 및 mock 함수
    const mockOnSubmit = vi.fn();
    render(<BacktestForm onSubmit={mockOnSubmit} />);
    
    // When: 사용자가 폼 작성 및 제출
    await userEvent.selectOptions(screen.getByLabelText('전략 선택'), 'SMA Crossover');
    await userEvent.type(screen.getByLabelText('티커'), '005930.KS');
    await userEvent.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // Then: submit 핸들러 호출 확인
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          strategy: 'SMA Crossover',
          ticker: '005930.KS'
        })
      );
    });
  });
  
  it('should show validation error when ticker is empty', async () => {
    // Given: 폼 렌더링
    render(<BacktestForm />);
    
    // When: 티커 입력 없이 제출
    await userEvent.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // Then: 에러 메시지 표시
    expect(await screen.findByText('티커를 입력해주세요')).toBeInTheDocument();
  });
});
```

### 2. 커스텀 훅 테스트

```typescript
// features/backtest/hooks/useBacktestForm.test.ts
import { renderHook, act } from '@testing-library/react';
import { useBacktestForm } from './useBacktestForm';

describe('useBacktestForm', () => {
  it('should initialize with default values', () => {
    // When: 훅 렌더링
    const { result } = renderHook(() => useBacktestForm());
    
    // Then: 초기값 확인
    expect(result.current.formData.strategy).toBe('');
    expect(result.current.formData.ticker).toBe('');
    expect(result.current.errors).toEqual({});
  });
  
  it('should update form data when input changes', () => {
    // Given: 훅 렌더링
    const { result } = renderHook(() => useBacktestForm());
    
    // When: 입력 변경
    act(() => {
      result.current.handleChange('ticker', '005930.KS');
    });
    
    // Then: 상태 업데이트 확인
    expect(result.current.formData.ticker).toBe('005930.KS');
  });
  
  it('should validate form before submit', () => {
    // Given: 훅 렌더링
    const { result } = renderHook(() => useBacktestForm());
    
    // When: 빈 폼으로 제출 시도
    act(() => {
      result.current.handleSubmit();
    });
    
    // Then: 유효성 검사 에러 발생
    expect(result.current.errors.ticker).toBe('티커를 입력해주세요');
  });
});
```

### 3. API 클라이언트 모킹 (MSW)

```typescript
// test/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // 백테스트 실행 API 모킹
  http.post('/api/v1/backtest', async ({ request }) => {
    const body = await request.json();
    
    // 유효한 요청인 경우 성공 응답
    if (body.ticker && body.strategy) {
      return HttpResponse.json({
        total_return: 0.15,
        sharpe_ratio: 1.2,
        max_drawdown: -0.08,
        trades: []
      });
    }
    
    // 잘못된 요청인 경우 에러 응답
    return HttpResponse.json(
      { error: 'Invalid request' },
      { status: 400 }
    );
  }),
  
  // 전략 목록 조회 API 모킹
  http.get('/api/v1/strategies', () => {
    return HttpResponse.json([
      { id: 'sma_crossover', name: 'SMA Crossover' },
      { id: 'rsi', name: 'RSI Strategy' }
    ]);
  })
];
```

```typescript
// test/setup.ts
import { setupServer } from 'msw/node';
import { handlers } from './mocks/handlers';

export const server = setupServer(...handlers);

// 테스트 시작 전 MSW 서버 시작
beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

### 4. 통합 테스트: 전체 폼 워크플로

```typescript
// features/backtest/BacktestPage.test.tsx
describe('BacktestPage Integration', () => {
  it('should complete full backtest workflow', async () => {
    // Given: 페이지 렌더링
    render(<BacktestPage />);
    
    // When: 사용자가 폼 작성
    await userEvent.selectOptions(screen.getByLabelText('전략 선택'), 'SMA Crossover');
    await userEvent.type(screen.getByLabelText('티커'), '005930.KS');
    await userEvent.type(screen.getByLabelText('시작일'), '2023-01-01');
    await userEvent.type(screen.getByLabelText('종료일'), '2023-12-31');
    
    // When: 백테스트 실행
    await userEvent.click(screen.getByRole('button', { name: '백테스트 실행' }));
    
    // Then: 로딩 표시
    expect(screen.getByText('백테스트 실행 중...')).toBeInTheDocument();
    
    // Then: 결과 표시
    await waitFor(() => {
      expect(screen.getByText('총 수익률: 15.00%')).toBeInTheDocument();
      expect(screen.getByText('샤프 비율: 1.20')).toBeInTheDocument();
    });
  });
});
```

### 5. 컴포넌트 테스트 시 주의사항

**❌ 피해야 할 것**:
- 내부 구현 세부사항 테스트 (예: state 변수명, 내부 함수 호출)
- 스타일/레이아웃 테스트 (CSS, 버튼 색상 등)
- 과도한 snapshot 테스트

**✅ 해야 할 것**:
- 사용자 행동 시뮬레이션 (클릭, 타이핑 등)
- 렌더링 결과 검증 (텍스트, 요소 존재 여부)
- API 호출 검증
---

## 백테스팅 프로젝트 핵심 기능 테스트 우선순위

### 🔴 최우선 (반드시 작성)

1. **백테스팅 계산 로직** (단위 테스트)
   - 각 전략의 시그널 생성 로직 (RSI, MACD, SMA, 볼린저 밴드 등)
   - 수익률, Sharpe Ratio, MDD 계산
   - pandas Timedelta 변환 (backtesting.py 호환성)

2. **백테스트 실행 API** (통합 테스트)
   - POST /api/v1/backtest 엔드포인트
   - 정상 응답 및 에러 핸들링
   - 요청 검증 (Pydantic 모델)

3. **데이터 수집 및 캐싱** (통합 테스트)
   - yfinance 데이터 조회 및 DB 저장
   - 캐시 히트/미스 시나리오

### 🟡 중요 (가능하면 작성)

4. **전략 관리 API** (통합 테스트)
   - 전략 목록 조회
   - 전략별 파라미터 검증

5. **차트 데이터 변환** (단위 테스트)
   - DataFrame → JSON 변환
   - 날짜 포맷팅

6. **프론트엔드 폼 검증** (컴포넌트 테스트)
   - BacktestForm 유효성 검사
   - 사용자 입력 핸들링

### 🟢 선택 (시간이 남으면)

7. **뉴스 API** (통합 테스트)
8. **포트폴리오 관리** (단위 테스트)
9. **E2E 테스트** (1~2개 시나리오)

---

## 테스트 실행 및 커버리지

### 백엔드 테스트 실행

```bash
# Docker 컨테이너 내에서 실행
docker compose -f compose.dev.yaml exec backtest-be-fast bash

# 모든 테스트 실행
pytest

# 특정 테스트만 실행
pytest tests/unit/test_rsi_strategy.py

# 키워드로 필터링
pytest -k "backtest"

# 커버리지 리포트
pytest --cov=app --cov-report=html

# 마커로 분류 실행
pytest -m unit            # 단위 테스트만
pytest -m integration     # 통합 테스트만
pytest -m "not slow"      # 느린 테스트 제외
```

### 프론트엔드 테스트 실행

```bash
# 테스트 실행
npm run test:run

# watch 모드 (파일 변경 시 자동 재실행)
npm run test:watch

# UI 모드 (브라우저에서 확인)
npm run test:ui

# 커버리지
npm run test:coverage
```

### pytest 마커 사용 (conftest.py)

```python
# tests/conftest.py
import pytest

def pytest_configure(config):
    """커스텀 마커 등록"""
    config.addinivalue_line("markers", "unit: 단위 테스트")
    config.addinivalue_line("markers", "integration: 통합 테스트")
    config.addinivalue_line("markers", "slow: 느린 테스트 (5초 이상)")

# 테스트에 마커 적용
@pytest.mark.unit
def test_rsi_calculation():
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_full_backtest_workflow():
    pass
```

---

## 졸업 작품 일정에 맞는 현실적인 전략

### 1단계: 핵심 로직만 테스트 (1주차)
- [ ] RSI, SMA 등 주요 전략 2~3개의 계산 로직 단위 테스트
- [ ] 백테스트 실행 API 통합 테스트 1개
- **목표**: 가장 중요한 기능의 정확성 보장

### 2단계: API 계약 검증 (2주차)
- [ ] 모든 엔드포인트의 정상/에러 케이스 테스트
- [ ] Pydantic 모델 직렬화 테스트
- **목표**: 프론트엔드-백엔드 통신 안정성 확보

### 3단계: 프론트엔드 핵심 컴포넌트 (3주차)
- [ ] BacktestForm 검증 로직 테스트
- [ ] 커스텀 훅 (useBacktestForm) 테스트
- **목표**: 사용자 입력 처리 안정성 확보

### 4단계: 선택적 보완 (4주차, 시간이 있을 때만)
- [ ] 나머지 전략 로직 단위 테스트
- [ ] E2E 테스트 1~2개 시나리오
- [ ] 커버리지 80% 이상 달성

> **중요**: 완벽한 테스트 커버리지보다는 **핵심 기능의 신뢰성**이 우선!  
> 시간이 부족하면 1~2단계만 완료해도 충분히 가치 있는 테스트

---

## 팀 협업 시 테스트 전략

### Git Workflow와 테스트

```bash
# 1. 새 기능 브랜치 생성
git checkout -b feature/rsi-strategy

# 2. 코드 작성 및 테스트 작성
# ...

# 3. 테스트 실행 확인
pytest tests/unit/test_rsi_strategy.py

# 4. 커밋 (테스트 통과 후에만)
git add .
git commit -m "feat: RSI 전략 구현 및 테스트 추가"

# 5. PR 생성 전 전체 테스트 실행
pytest
```

### GitHub Actions CI 설정 (선택)

```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          docker compose -f compose.dev.yaml up -d backtest-be-fast
          docker compose -f compose.dev.yaml exec -T backtest-be-fast pytest
  
  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: cd backtest_fe && npm ci
      - run: cd backtest_fe && npm run test:run
```

---

## 테스트 작성 시 자주 묻는 질문 (FAQ)

### Q1. 모든 함수를 테스트해야 하나요?
**A**: 아니오. 단순 getter/setter, 프레임워크 기본 기능은 테스트하지 않습니다.  
**테스트 대상**: 계산 로직, 비즈니스 규칙, API 계약, 데이터 변환

### Q2. 테스트 커버리지 목표는?
**A**: 졸업 작품에서는 **50~70%**면 충분합니다.  
100%를 목표로 하면 시간 낭비이며, 핵심 기능만 집중적으로 테스트하세요.

### Q3. Mock을 언제 사용하나요?
**A**: 
- ✅ 외부 API (yfinance, Naver Search)
- ✅ 느린 연산 (DB 대량 조회)
- ❌ 내부 비즈니스 로직 (실제 객체 사용 권장)

### Q4. 테스트가 실패하면 어떻게 하나요?
**A**: 
1. 에러 메시지를 읽고 어느 부분이 실패했는지 파악
2. 테스트가 잘못된 건지, 프로덕션 코드가 잘못된 건지 판단
3. 디버거 또는 print문으로 중간 값 확인
4. Given-When-Then 단계별로 나눠서 문제 격리

### Q5. TDD를 반드시 해야 하나요?
**A**: 아니요. 졸업 작품에서는 **코드 작성 후 테스트 작성**도 괜찮습니다.  
단, 복잡한 계산 로직은 테스트를 먼저 작성하면 요구사항 정리에 도움이 됩니다.

---

## 결론

백테스팅 플랫폼에서 테스트 코드의 핵심 가치는 **금융 계산의 정확성**과 **데이터 무결성** 보장입니다.

**기억해야 할 핵심 원칙**:
1. ✅ **가치 중심**: 핵심 20% 기능에 집중하여 80% 신뢰성 확보
2. ✅ **실용성**: 졸업 작품 일정 내에서 실현 가능한 범위만 작성
3. ✅ **유지보수성**: 구현에 강결합되지 않도록 결과와 행동 검증
4. ✅ **FIRST 원칙**: 빠르고, 독립적이며, 반복 가능하고, 자가 검증되며, 적시에 작성

**현실적인 목표**:
- 단위 테스트: 전략 로직, 계산 함수 → **20~30개**
- 통합 테스트: API 엔드포인트 → **10~15개**
- 컴포넌트 테스트: 핵심 폼 컴포넌트 → **5~10개**
- E2E 테스트: 선택적 (1~2개 시나리오)

> 💡 **"완벽한 테스트보다 올바른 테스트가 중요합니다"**  
> 모든 코드를 테스트하려 하지 말고, 시스템의 신뢰성을 보장하는 핵심 기능에만 집중하세요.

---

## 참고 문헌

[1] [TDD] 단위 테스트(Unit Test) 작성의 필요성 - MangKyu's Diary  
https://mangkyu.tistory.com/143

[2] 가치있는 테스트를 위한 전략과 구현 - Toss Tech  
https://toss.tech/article/test-strategy-server

[3] 테스트 코드 작성 가이드(근데 이제 Jest를 곁들인) - 비브로스 기술 블로그  
https://boostbrothers.github.io/2025-01-22-test-code-guide/

[4] [Java] JUnit을 활용한 Java 단위 테스트 코드 작성법 - MangKyu's Diary  
https://mangkyu.tistory.com/144

[5] 테스팅 - FastAPI 공식 문서  
https://fastapi.tiangolo.com/ko/tutorial/testing/

---

**문서 작성일**: 2025-10-12  
**문서 버전**: 2.0 (백테스팅 프로젝트 특화)  
**작성자**: GitHub Copilot
________________________________________
[1] [TDD] 단위 테스트(Unit Test) 작성의 필요성 (1/3) - MangKyu's Diary
https://mangkyu.tistory.com/143
[2] [7] [8] [9] 가치있는 테스트를 위한 전략과 구현
https://toss.tech/article/test-strategy-server
[3] [4] [10] [11] 테스트 코드 작성 가이드(근데 이제 Jest를 곁들인) | 비브로스 기술 블로그
https://boostbrothers.github.io/2025-01-22-test-code-guide/
[5] [6] [Java] JUnit을 활용한 Java 단위 테스트 코드 작성법 (2/3) - MangKyu's Diary
https://mangkyu.tistory.com/144
[12]
https://mangkyu.tistory.com/145
[13]
https://sjh9708.tistory.com/240
[17] [18] 테스팅 - FastAPI
https://fastapi.tiangolo.com/ko/tutorial/testing/
