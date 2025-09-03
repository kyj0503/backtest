# 테스트 가이드

백테스팅 시스템의 종합적인 테스트 전략과 실행 방법을 설명합니다.

## 테스트 아키텍처

### 테스트 피라미드
```
     /\
    /  \     E2E (5%)
   /____\    전체 워크플로우
  /      \   
 /        \  Integration (25%)
/__________\ API 엔드포인트
/          \
/            \ Unit (70%)
\____________/ 개별 함수/클래스
```

## 백엔드 테스트

### 디렉터리 구조
```
backend/tests/
├── conftest.py              # 공통 픽스처
├── fixtures/                # 테스트 데이터
│   ├── mock_data.py        # 모킹 데이터
│   └── expected_results.py # 예상 결과
├── unit/                   # 단위 테스트
│   ├── test_strategy_service.py
│   ├── test_data_fetcher.py
│   └── test_backtest_service.py
├── integration/            # 통합 테스트
│   ├── test_api_endpoints.py
│   └── test_backtest_flow.py
└── e2e/                   # E2E 테스트
    └── test_complete_backtest.py
```

### 완전 오프라인 모킹
CI/CD 안정성을 위해 모든 외부 의존성을 모킹합니다.

```python
# conftest.py
@pytest.fixture
def mock_yfinance_data():
    """yfinance 데이터 모킹"""
    with patch('yfinance.download') as mock_download:
        mock_download.return_value = create_mock_stock_data()
        yield mock_download

@pytest.fixture
def mock_mysql_connection():
    """MySQL 연결 모킹"""
    with patch('app.services.yfinance_db.get_connection') as mock_conn:
        mock_conn.return_value = create_mock_connection()
        yield mock_conn
```

### 테스트 실행
```bash
# 전체 테스트
docker-compose exec backend pytest tests/ -v

# 단위 테스트만
pytest tests/unit/ -v

# 통합 테스트만
pytest tests/integration/ -v

# 커버리지 포함
pytest tests/ --cov=app --cov-report=html
```

### 현재 테스트 상태
- **통과율**: 65/68 (95.3%)
- **정상 스킵**: 3개
- **커버리지**: 85%+

## 프론트엔드 테스트

### 디렉터리 구조
```
frontend/src/test/
├── components/              # 컴포넌트 테스트
│   ├── UnifiedBacktestForm.test.tsx
│   └── BacktestResult.test.tsx
├── services/                # 서비스 테스트
│   └── api.test.ts
└── utils/                   # 유틸리티 테스트
    └── formatters.test.ts
```

### 테스트 도구
- **Vitest**: 테스트 러너
- **Testing Library**: React 컴포넌트 테스트
- **MSW**: API 모킹

### 테스트 실행
```bash
# 개발 환경에서 테스트
docker-compose exec frontend npm test

# CI/CD 환경에서 테스트
npm test -- --run

# 커버리지 포함
npm test -- --coverage
```

### 현재 테스트 상태
- **통과율**: 23/23 (100%)
- **커버리지**: 75%+

## 모킹 전략

### 백엔드 모킹
```python
def create_mock_stock_data():
    """현실적인 주식 데이터 생성"""
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='D')
    
    # 기하 브라운 운동으로 가격 시뮬레이션
    prices = []
    current_price = 100.0
    
    for date in dates:
        if date.weekday() < 5:  # 주중만
            drift = 0.0002
            volatility = 0.02
            shock = np.random.normal(0, 1)
            
            current_price *= (1 + drift + volatility * shock)
            prices.append({
                'Date': date,
                'Open': current_price * 0.999,
                'High': current_price * 1.01,
                'Low': current_price * 0.995,
                'Close': current_price,
                'Volume': np.random.randint(1000000, 10000000)
            })
    
    return pd.DataFrame(prices).set_index('Date')
```

### 프론트엔드 모킹
```typescript
// MSW를 사용한 API 모킹
import { rest } from 'msw';

export const handlers = [
  rest.post('/api/v1/backtest', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        portfolio_statistics: {
          Total_Return: 23.46,
          Sharpe_Ratio: 1.23
        }
      })
    );
  })
];
```

## 테스트 데이터

### 시나리오 기반 테스트
```python
# fixtures/test_scenarios.json
{
  "bull_market": {
    "description": "강세장 시나리오",
    "start_price": 100,
    "end_price": 150,
    "volatility": 0.15,
    "trend": "upward"
  },
  "bear_market": {
    "description": "약세장 시나리오",
    "start_price": 100,
    "end_price": 70,
    "volatility": 0.25,
    "trend": "downward"
  },
  "volatile_market": {
    "description": "변동성 시장",
    "start_price": 100,
    "end_price": 105,
    "volatility": 0.35,
    "trend": "sideways"
  }
}
```

## CI/CD 테스트 파이프라인

### Jenkins 파이프라인
```groovy
stage('Backend Tests') {
    steps {
        dir('backend') {
            sh 'pip install -r requirements-test.txt'
            sh 'pytest tests/ -v --cov=app --junitxml=test-results.xml'
        }
    }
    post {
        always {
            publishTestResults(
                testResultsPattern: 'backend/test-results.xml'
            )
        }
    }
}

stage('Frontend Tests') {
    steps {
        dir('frontend') {
            sh 'npm ci'
            sh 'npm test -- --run --reporter=junit'
            sh 'npm run build'
        }
    }
    post {
        always {
            publishTestResults(
                testResultsPattern: 'frontend/test-results.xml'
            )
        }
    }
}
```

## 성능 테스트

### 백엔드 성능 테스트
```python
import time
import pytest

def test_backtest_performance():
    """백테스트 실행 시간 측정"""
    start_time = time.time()
    
    # 백테스트 실행
    result = run_backtest(large_portfolio)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # 5초 이내 완료 확인
    assert execution_time < 5.0
    assert result.success is True
```

### 프론트엔드 성능 테스트
```typescript
import { render, screen } from '@testing-library/react';
import { performance } from 'perf_hooks';

test('chart rendering performance', () => {
  const startTime = performance.now();
  
  render(<OHLCChart data={largeDataset} />);
  
  const endTime = performance.now();
  const renderTime = endTime - startTime;
  
  // 1초 이내 렌더링 확인
  expect(renderTime).toBeLessThan(1000);
});
```

## 테스트 베스트 프랙티스

### 1. 테스트 작성 규칙
```python
def test_should_calculate_correct_return_when_price_increases():
    # Given (준비)
    initial_price = 100.0
    final_price = 120.0
    
    # When (실행)
    return_pct = calculate_return(initial_price, final_price)
    
    # Then (검증)
    assert return_pct == 20.0
```

### 2. 모킹 원칙
- **외부 의존성만 모킹**: 내부 로직은 실제 코드 사용
- **일관된 모킹 데이터**: 현실적이고 예측 가능한 데이터
- **모킹 범위 최소화**: 필요한 부분만 모킹

### 3. 테스트 격리
```python
@pytest.fixture(autouse=True)
def reset_cache():
    """각 테스트마다 캐시 초기화"""
    cache.clear()
    yield
    cache.clear()
```

## 디버깅 도구

### 테스트 디버깅
```bash
# 특정 테스트만 실행
pytest tests/unit/test_strategy_service.py::test_sma_strategy -v

# 디버깅 모드로 실행
pytest tests/ -v -s --pdb

# 로그 출력 포함
pytest tests/ -v --log-cli-level=DEBUG
```

### 테스트 커버리지 확인
```bash
# HTML 리포트 생성
pytest tests/ --cov=app --cov-report=html

# 브라우저에서 확인
open htmlcov/index.html
```

## 문제 해결

### 일반적인 테스트 문제

1. **모킹 데이터 불일치**
   - 원인: 실제 API 응답과 모킹 데이터 형식 차이
   - 해결: 실제 응답을 기반으로 모킹 데이터 작성

2. **비동기 테스트 실패**
   - 원인: async/await 처리 누락
   - 해결: pytest-asyncio 사용, @pytest.mark.asyncio 데코레이터 추가

3. **타임존 관련 오류**
   - 원인: 로컬과 CI 환경의 타임존 차이
   - 해결: UTC 기준으로 통일, freeze_time 사용

### 테스트 성능 최적화
```python
# 병렬 테스트 실행
pytest tests/ -n auto

# 빠른 실패 모드
pytest tests/ -x

# 캐시 사용
pytest tests/ --cache-dir=.pytest_cache
```

## 향후 개선 계획

### 단기 (테스트 품질)
- [ ] 테스트 커버리지 90% 달성
- [ ] E2E 테스트 시나리오 확장
- [ ] 성능 테스트 자동화

### 중기 (테스트 효율성)
- [ ] Visual Regression 테스트 도입
- [ ] Property-based 테스트 적용
- [ ] 테스트 데이터 팩토리 패턴 구현

### 장기 (테스트 인프라)
- [ ] 테스트 환경 자동 프로비저닝
- [ ] A/B 테스트 프레임워크 구축
- [ ] 카나리 배포 테스트 자동화
