# Backend Test Suite

백테스팅 백엔드의 테스트 스위트입니다. 핵심 단위 테스트를 포함합니다.

## 테스트 구조

```
tests/
├── unit/               # 단위 테스트 (DB 없이 실행 가능)
│   ├── test_sma_strategy.py
│   ├── test_rsi_strategy.py
│   ├── test_macd_strategy.py
│   ├── test_ema_strategy.py
│   ├── test_bollinger_strategy.py
│   ├── test_buy_hold_strategy.py
│   ├── test_chart_data_service.py
│   ├── test_strategy_service.py
│   ├── test_request_models.py
│   └── test_portfolio_schemas.py
├── integration/        # 통합 테스트 (API + DB 필요)
│   └── test_backtest_api.py
├── e2e/               # End-to-end 테스트
│   └── validate_backtest_results.py
├── fixtures/          # 테스트 데이터 팩토리
│   └── backtest_fixtures.py
└── conftest.py        # 전역 pytest 설정 및 fixtures
```

## 테스트 실행

### Docker 환경 (권장)

```bash
# 백엔드 컨테이너에서 테스트 실행
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit -v

# 특정 테스트 파일 실행
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit/test_sma_strategy.py -v

# 커버리지 포함 실행
docker compose -f compose.dev.yaml exec backtest-be-fast pytest tests/unit --cov=app --cov-report=html
```

### 로컬 환경

```bash
cd backtest_be_fast

# 가상환경 활성화 (선택사항)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
pip install -r requirements-test.txt

# 단위 테스트 실행 (DB 불필요)
pytest tests/unit -v

# 마커별 실행
pytest -m unit          # 단위 테스트만
pytest -m integration   # 통합 테스트만 (DB 필요)
pytest -m "not integration"  # DB 없이 실행 가능한 테스트만
```

## 테스트 범위

### 전략 테스트 (Strategy Tests)
각 전략의 계산 로직과 매매 시그널 생성을 검증합니다.

- **SMA Strategy** (`test_sma_strategy.py`): 이동평균 교차 전략
  - SMA 계산 정확성
  - 골든 크로스/데드 크로스 시그널
  - 포지션 크기 조절

- **RSI Strategy** (`test_rsi_strategy.py`): 상대강도지수 전략
  - RSI 계산 (0-100 범위)
  - 과매수/과매도 구간 판별
  - 다이버전스 감지

- **MACD Strategy** (`test_macd_strategy.py`): MACD 지표 전략
  - MACD, Signal, Histogram 계산
  - 매수/매도 크로스오버

- **Bollinger Bands** (`test_bollinger_strategy.py`): 볼린저 밴드 전략
  - 상/하단 밴드 계산
  - 밴드 이탈/회귀 시그널

- **EMA Strategy** (`test_ema_strategy.py`): 지수이동평균 전략
  - EMA 계산 (최근 가격 가중치)
  - EMA 교차 시그널

- **Buy & Hold** (`test_buy_hold_strategy.py`): 매수 후 보유 전략
  - 최소 거래 검증
  - 장기 보유 수익률

### 서비스 테스트 (Service Tests)

- **Chart Data Service** (`test_chart_data_service.py`): 차트 데이터 생성
  - OHLC 데이터 변환
  - 거래 마커 생성
  - 기술 지표 직렬화

- **Strategy Service** (`test_strategy_service.py`): 전략 관리
  - 전략 파라미터 검증
  - 전략 클래스 로드

### 스키마 테스트 (Schema Tests)

- **Request Models** (`test_request_models.py`): API 요청 검증
  - Pydantic 모델 검증
  - 파라미터 타입 체크

- **Portfolio Schemas** (`test_portfolio_schemas.py`): 포트폴리오 모델
  - 포트폴리오 구성 검증
  - 리밸런싱 로직

## 테스트 현황

총 **68개 단위 테스트** (통합/E2E 제외)

| 카테고리 | 테스트 수 | 상태 |
|---------|----------|------|
| 전략 테스트 | 45+ | 통과 |
| 서비스 테스트 | 15+ | 통과 |
| 스키마 테스트 | 8+ | 통과 |

## 테스트 특징

현재 테스트 스위트의 주요 특징은 다음과 같습니다:

- **핵심 비즈니스 로직 커버**: 모든 전략의 계산 로직 테스트
- **단위 테스트 위주**: DB 없이 빠르게 실행 가능
- **Given-When-Then 패턴**: 읽기 쉬운 테스트 구조
- **경계값 테스트**: 엣지 케이스 검증
- **Mock 활용**: 외부 의존성 격리

## 개선 사항 (v1.6.6)

1. **conftest.py 단순화**
   - SQLAlchemy를 optional import로 변경
   - 단위 테스트에서 DB 의존성 제거
   - Mock fixtures로 외부 서비스 격리

2. **테스트 분리**
   - 단위 테스트: `tests/unit/` (DB 불필요)
   - 통합 테스트: `tests/integration/` (DB 필요)
   - E2E 테스트: `tests/e2e/` (전체 스택)

3. **실행 성능 향상**
   - 단위 테스트만 실행 시 수 초 내 완료
   - DB 설정 없이도 테스트 가능

## 테스트 작성 가이드

### 새 전략 테스트 추가

```python
# tests/unit/test_my_strategy.py
import pytest
import pandas as pd
from backtesting import Backtest
from app.strategies.my_strategy import MyStrategy

class TestMyStrategy:
    """My Strategy 단위 테스트"""

    def create_sample_data(self, close_prices):
        """테스트용 OHLC 데이터 생성"""
        dates = pd.date_range(start='2023-01-01', periods=len(close_prices), freq='D')
        return pd.DataFrame({
            'Open': close_prices,
            'High': close_prices * 1.01,
            'Low': close_prices * 0.99,
            'Close': close_prices,
            'Volume': [1000000] * len(close_prices)
        }, index=dates)

    def test_strategy_basic_functionality(self):
        """Given: 가격 데이터
        When: 전략 실행
        Then: 거래 발생"""
        # Given
        close_prices = pd.Series([100, 105, 110, 115, 120])
        data = self.create_sample_data(close_prices)

        # When
        bt = Backtest(data, MyStrategy, cash=10000, commission=0.0)
        result = bt.run()

        # Then
        assert result is not None
        assert '# Trades' in result
```

### 서비스 테스트 추가

```python
# tests/unit/test_my_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.my_service import MyService

@pytest.fixture
def my_service():
    return MyService()

class TestMyService:
    """My Service 단위 테스트"""

    def test_service_method(self, my_service):
        """Given: 입력 데이터
        When: 서비스 메서드 호출
        Then: 예상 결과 반환"""
        # Given
        input_data = {"key": "value"}

        # When
        result = my_service.process(input_data)

        # Then
        assert result["status"] == "success"
```

## 테스트 실패 시 디버깅

```bash
# 상세한 오류 메시지 출력
pytest tests/unit/test_sma_strategy.py -vv

# 특정 테스트만 실행
pytest tests/unit/test_sma_strategy.py::TestSMACalculation::test_sma_calculates_correct_value -v

# 실패한 테스트만 재실행
pytest --lf

# pdb 디버거로 실행
pytest --pdb
```

## 참고 자료

- [Pytest Documentation](https://docs.pytest.org/)
- [Backtesting.py Documentation](https://kernc.github.io/backtesting.py/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
