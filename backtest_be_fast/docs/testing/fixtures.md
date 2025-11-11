# 픽스처 및 테스트 데이터

테스트의 일관성과 재사용성을 높이기 위해 `pytest`의 픽스처(fixture) 시스템과 팩토리 패턴을 적극적으로 활용합니다. 이를 통해 테스트 설정 코드를 중앙에서 관리하고, 각 테스트는 필요한 데이터와 환경을 선언적으로 주입받을 수 있습니다.

## 1. Pytest 픽스처 (`conftest.py`)

픽스처는 테스트 함수에 전달되는 인자(argument)로, 테스트 실행 전후에 필요한 설정 및 정리 작업을 수행합니다. 프로젝트의 핵심 픽스처는 `tests/conftest.py`에 정의되어 있으며, 모든 테스트에서 공유됩니다.

### 주요 픽스처

-   **`mock_db_session`**:
    -   **역할**: 실제 데이터베이스 대신 인메모리 SQLite 데이터베이스 세션을 생성하고 제공합니다.
    -   **범위**: `function` (각 테스트 함수마다 독립적인 세션 생성)
    -   **장점**: 테스트가 데이터베이스 상태에 대해 서로 영향을 주지 않도록 격리합니다. 실행 속도가 빠릅니다.

-   **`mock_strategy_service`**:
    -   **역할**: `StrategyService`의 의존성을 모킹(mocking)하여, 특정 전략 클래스를 반환하도록 제어합니다.
    -   **사용처**: `BacktestService`나 `PortfolioService`와 같이 전략 클래스를 동적으로 로드하는 서비스를 테스트할 때 사용됩니다.

-   **`sample_ticker_data`**:
    -   **역할**: 백테스트에 필요한 표준 형식의 `pd.DataFrame` 데이터를 제공합니다.
    -   **내용**: 'Open', 'High', 'Low', 'Close', 'Volume' 컬럼을 포함하는 샘플 시계열 데이터를 반환합니다.
    -   **장점**: 여러 테스트에서 동일한 형식의 입력 데이터를 재사용하여 일관성을 유지합니다.

### 픽스처 사용법

테스트 함수에서 픽스처의 이름을 인자로 선언하기만 하면 `pytest`가 자동으로 해당 픽스처를 실행하고 그 결과를 주입해줍니다.

```python
# tests/unit/services/test_backtest_service.py

def test_run_backtest_with_mock_data(
    mock_db_session, # DB 세션 픽스처 주입
    sample_ticker_data # 샘플 데이터 픽스처 주입
):
    # ... 테스트 로직 ...
    # mock_db_session과 sample_ticker_data를 사용하여 서비스 테스트
    pass
```

## 2. 테스트 데이터 팩토리 (`tests/fixtures/`)

정적인 픽스처만으로는 다양한 테스트 시나리오에 대응하기 어렵습니다. 예를 들어, 특정 필드 값만 다른 여러 종류의 API 요청 객체를 테스트해야 할 수 있습니다. 이때 **팩토리 패턴**을 사용하면 필요한 데이터를 동적으로 생성할 수 있습니다.

-   **위치**: `tests/fixtures/` 디렉토리에는 `factory-boy` 라이브러리를 사용한 팩토리 클래스들이 정의되어 있습니다.
-   **예시**: `BacktestRequestFactory`

```python
# tests/fixtures/factories.py
import factory
from app.schemas.requests import BacktestRequest, PortfolioAsset

class PortfolioAssetFactory(factory.Factory):
    class Meta:
        model = PortfolioAsset
    
    ticker = "AAPL"
    weight = factory.LazyAttribute(lambda o: 0.5)

class BacktestRequestFactory(factory.Factory):
    class Meta:
        model = BacktestRequest

    strategy_name = "sma"
    start_date = "2022-01-01"
    end_date = "2023-01-01"
    initial_capital = 10000.0
    
    # 포트폴리오 자산 목록을 동적으로 생성
    assets = factory.List([
        factory.SubFactory(PortfolioAssetFactory, ticker="AAPL", weight=0.5),
        factory.SubFactory(PortfolioAssetFactory, ticker="GOOG", weight=0.5),
    ])
```

### 팩토리 사용법

테스트 코드 내에서 팩토리를 호출하여 필요한 데이터를 생성합니다. 특정 필드의 값을 오버라이드하여 원하는 시나리오에 맞는 데이터를 쉽게 만들 수 있습니다.

```python
# tests/integration/api/test_backtest_api.py

def test_invalid_portfolio_weight(client):
    # 유효하지 않은 요청 데이터 생성 (가중치의 합이 1이 아님)
    invalid_request_data = BacktestRequestFactory(
        assets=[
            {"ticker": "AAPL", "weight": 0.7},
            {"ticker": "MSFT", "weight": 0.7},
        ]
    )

    response = client.post("/api/v1/portfolio/backtest", json=invalid_request_data.dict())
    
    assert response.status_code == 422 # Unprocessable Entity
```

## 결론

-   **픽스처**는 테스트의 **환경과 공유 자원**을 설정하는 데 사용됩니다. (예: DB 연결, 모킹된 서비스)
-   **팩토리**는 테스트에 필요한 **입력 데이터**를 동적이고 유연하게 생성하는 데 사용됩니다. (예: API 요청 본문, 모델 객체)

이 두 가지를 조합하여 테스트 코드의 중복을 줄이고, 다양한 시나리오를 효율적으로 커버하며, 테스트의 의도를 명확하게 표현할 수 있습니다.
