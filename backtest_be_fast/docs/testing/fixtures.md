# 픽스처 및 테스트 데이터

테스트의 일관성과 재사용성을 높이기 위해 `pytest`의 픽스처(fixture) 시스템과 팩토리 패턴을 적극적으로 활용합니다. 이를 통해 테스트 설정 코드를 중앙에서 관리하고, 각 테스트는 필요한 데이터와 환경을 선언적으로 주입받을 수 있습니다.

## 1. Pytest 픽스처 (`conftest.py`)

픽스처는 테스트 함수에 전달되는 인자(argument)로, 테스트 실행 전후에 필요한 설정 및 정리 작업을 수행합니다. 프로젝트의 핵심 픽스처는 `tests/conftest.py`에 정의되어 있으며, 모든 테스트에서 공유됩니다.

### 주요 픽스처

아래는 실제 `tests/conftest.py`에 정의된 픽스처입니다 (모두 `tests/unit`, `tests/integration`에서 공유됩니다).

-   **`db_session`** / **`db_engine`**:
    -   **역할**: `sqlalchemy.ext.asyncio`의 `AsyncSession`/`create_async_engine`을 사용하는, **통합 테스트 전용** DB 픽스처입니다. `test_settings`가 제공하는 `DATABASE_URL`(`mysql+aiomysql://...`)로 연결하며, SQLite가 아니라 실제 MySQL을 가리킵니다.
    -   **범위**: `db_engine`은 `session`, `db_session`은 `function`.
    -   `sqlalchemy`나 `httpx`가 설치되어 있지 않으면 `pytest.skip()`으로 건너뜁니다.

-   **`client`**:
    -   **역할**: `httpx.AsyncClient(app=app, base_url="http://test")`를 사용하는 비동기 HTTP 클라이언트 픽스처입니다. 이름이 `client`이며 `async_client`가 아닙니다.
    -   **참고**: 현재 `tests/integration/test_backtest_api.py`와 `tests/unit/test_portfolio_backtest_error_contract.py`는 이 픽스처를 쓰지 않고, 파일 상단에서 `client = TestClient(app)`(`fastapi.testclient`, 동기)를 직접 만들어 사용합니다. `client` 픽스처는 conftest에 정의는 되어 있지만 현재 테스트 스위트에서 실사용처는 없습니다.

-   **`mock_data_repository`** / **`mock_yfinance_service`**:
    -   **역할**: 각각 데이터 리포지토리와 Yahoo Finance 서비스를 흉내 내는 `unittest.mock.Mock`/`AsyncMock` 객체를 제공합니다 (`get_price_data`, `save_price_data`, `download` 등 몇 개 메서드만 스텁되어 있음).

-   **`sample_backtest_request`** / **`sample_portfolio_data`** / **`sample_price_data`**:
    -   **역할**: 각각 백테스트 요청 dict, 포트폴리오 dict, 3일치 OHLCV 리스트를 제공하는 정적 샘플 데이터 픽스처입니다. `sample_ticker_data`라는 이름의 픽스처는 없습니다.

-   **`freeze_time`** / **`faker`**:
    -   `freezegun`/`faker` 패키지가 설치되어 있을 때만 동작하며, 없으면 skip됩니다.

### 픽스처 사용법

테스트 함수에서 픽스처의 이름을 인자로 선언하기만 하면 `pytest`가 자동으로 해당 픽스처를 실행하고 그 결과를 주입해줍니다.

```python
# tests/unit/test_data_repository.py (실제 파일 기준 예시)

def test_something(mock_data_repository, sample_price_data):
    # ... mock_data_repository와 sample_price_data를 사용하여 검증 ...
    pass
```

## 2. 테스트 데이터 팩토리 (`tests/fixtures/`)

정적인 픽스처만으로는 다양한 테스트 시나리오에 대응하기 어렵습니다. 이때 **팩토리 패턴**을 사용하면 필요한 데이터를 동적으로 생성할 수 있습니다.

-   **위치**: `tests/fixtures/`에는 `factory-boy` 기반 팩토리와 헬퍼 함수가 두 파일로 나뉘어 있습니다 — `factories.py`라는 단일 파일이 아닙니다.
    -   `backtest_fixtures.py`: `BacktestRequestFactory`, `BacktestResultFactory`, `BacktestHistoryFactory` + `create_price_data()`, `create_equity_curve()`, `create_backtest_metrics()` 등의 헬퍼 함수.
    -   `portfolio_fixtures.py`: `PortfolioFactory`, `PositionFactory`, `TradeFactory` + `create_portfolio_data()`, `create_multiple_positions()` 등의 헬퍼 함수.
-   `app.schemas.requests`에는 `PortfolioAsset`이라는 모델이 없습니다. `requests.py`에는 `StrategyType`과 단일 종목용 `BacktestRequest`만 있습니다. 포트폴리오 요청 모델(`PortfolioBacktestRequest`, `PortfolioStock`)은 `app/schemas/schemas.py`에 정의되어 있고, `PortfolioBacktestRequest.portfolio`는 `List[PortfolioStock]`입니다.

### 팩토리 사용법

테스트 코드 내에서 팩토리나 헬퍼 함수를 호출해 필요한 데이터를 생성합니다. 실제 백테스트 API는 `POST /api/v1/backtest` 하나뿐입니다 (`POST /api/v1/portfolio/backtest`라는 경로는 존재하지 않습니다).

```python
# tests/integration/test_backtest_api.py 스타일 예시
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_portfolio_returns_422():
    payload = {
        "portfolio": [],  # 빈 포트폴리오는 검증 단계에서 거부됨
        "start_date": "2023-01-01",
        "end_date": "2023-06-30",
        "strategy": "buy_hold_strategy",
    }

    response = client.post("/api/v1/backtest", json=payload)

    assert response.status_code == 422  # Unprocessable Entity
```

## 결론

-   **픽스처**는 테스트의 **환경과 공유 자원**을 설정하는 데 사용됩니다. (예: DB 연결, 모킹된 서비스)
-   **팩토리**는 테스트에 필요한 **입력 데이터**를 동적이고 유연하게 생성하는 데 사용됩니다. (예: API 요청 본문, 모델 객체)

이 두 가지를 조합하여 테스트 코드의 중복을 줄이고, 다양한 시나리오를 효율적으로 커버하며, 테스트의 의도를 명확하게 표현할 수 있습니다.
