# 비동기 코드 테스트

FastAPI는 비동기(async/await) 기반 프레임워크이므로, 서비스와 API 로직의 상당 부분이 비동기 함수로 작성되어 있습니다. 이러한 비동기 코드를 올바르게 테스트하기 위해 `pytest-asyncio` 플러그인을 사용합니다.

## `pytest-asyncio` 설정

`pytest.ini` 파일에 `asyncio_mode = strict`로 설정되어 있습니다. 이는 `pytest`가 비동기 테스트를 자동으로 감지하고, 각 테스트를 독립적인 `asyncio` 이벤트 루프에서 실행하도록 보장하는 엄격한 모드입니다.

```ini
[pytest]
asyncio_mode = strict
```

## 비동기 테스트 작성법

### 1. `async def` 사용

테스트 함수를 일반적인 `def` 대신 `async def`로 선언합니다. 이를 통해 테스트 함수 내에서 `await` 키워드를 사용할 수 있습니다.

### 2. 비동기 함수 호출 시 `await` 사용

테스트 대상인 비동기 함수나 메서드를 호출할 때는 반드시 `await` 키워드를 붙여야 합니다. `await`를 생략하면 코루틴(coroutine) 객체만 반환되고 실제 코드는 실행되지 않아 테스트가 실패하거나 잘못된 결과를 낳을 수 있습니다.

### 예시: 비동기 서비스 테스트

`BacktestService`의 `run_backtest` 메서드는 내부적으로 `asyncio.to_thread`를 사용하여 동기 I/O 작업을 비동기적으로 처리합니다. 이 서비스를 테스트하는 코드는 다음과 같습니다.

```python
# tests/integration/services/test_backtest_service.py
import pytest
from app.services.backtest_service import backtest_service
from app.schemas.requests import BacktestRequest

@pytest.mark.integration
@pytest.mark.asyncio  # pytest-asyncio에게 이 테스트가 비동기임을 명시
async def test_run_backtest_async(sample_ticker_data_fixture):
    """
    BacktestService.run_backtest가 비동기적으로 올바르게 실행되는지 테스트합니다.
    """
    # given: 테스트 요청 데이터 준비
    request = BacktestRequest(
        strategy_name="sma",
        tickers=["AAPL"],
        start_date="2022-01-01",
        end_date="2023-01-01",
        initial_capital=10000,
        params={"sma_short": 10, "sma_long": 20}
    )

    # when: 비동기 서비스 메서드 호출
    # backtest_service.run_backtest는 async 함수이므로 await를 사용해야 합니다.
    result = await backtest_service.run_backtest(request)

    # then: 결과 검증
    assert result is not None
    assert "stats" in result
    assert result["stats"]["Sharpe Ratio"] > 0
```

-   `@pytest.mark.asyncio`: 이 마커는 `pytest-asyncio`에게 해당 테스트가 비동기임을 명시적으로 알려줍니다. `strict` 모드에서는 모든 `async def` 테스트에 이 마커를 붙이는 것이 권장됩니다.

## 비동기 API 엔드포인트 테스트

`httpx`의 `AsyncClient`를 사용하여 비동기 API 엔드포인트를 테스트할 수 있습니다. `conftest.py`에 `async_client` 픽스처를 정의하여 재사용할 수 있습니다.

### `async_client` 픽스처 예시

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture(scope="function")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

### 테스트 코드 예시

```python
# tests/e2e/test_portfolio_api.py
import pytest

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_portfolio_backtest_e2e(async_client):
    # given: 요청 데이터
    request_data = {
        # ... 포트폴리오 백테스트 요청 데이터 ...
    }

    # when: 비동기 클라이언트로 API 요청
    response = await async_client.post("/api/v1/portfolio/backtest", json=request_data)

    # then: 응답 검증
    assert response.status_code == 200
    result = response.json()
    assert "total_performance" in result
```

## 주의사항

-   **`asyncio.to_thread`와 레이스 컨디션**: 개발 중 동기 I/O 함수를 비동기 컨텍스트에서 직접 호출하면 레이스 컨디션이 발생할 수 있습니다. 모든 동기 I/O는 `asyncio.to_thread`로 감싸야 하며, 통합 테스트를 통해 이러한 문제가 없는지 검증하는 것이 중요합니다.
-   **모킹(Mocking)**: `unittest.mock`의 `AsyncMock`을 사용하여 비동기 의존성을 모킹할 수 있습니다. 이는 외부 API 호출과 같이 제어하기 어려운 비동기 작업을 모킹할 때 유용합니다.
