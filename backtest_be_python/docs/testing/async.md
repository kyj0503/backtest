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

### 예시: 비동기 서비스 테스트 (실제 코드)

`BacktestEngine.run_backtest`는 `async def`이며, 내부에서 `asyncio.to_thread`로 동기 I/O를 감쌉니다. 아래는 실제 `tests/unit/test_backtest_engine.py`에 있는 테스트를 그대로 옮긴 것입니다 (의존성은 전부 모킹되어 있어 `unit` 마커가 붙어 있습니다 — DB나 외부 API를 실제로 호출하는 것은 아닙니다).

```python
# tests/unit/test_backtest_engine.py
@pytest.mark.asyncio  # pytest-asyncio에게 이 테스트가 비동기임을 명시
async def test_run_backtest_success_returns_valid_result(
    self, mock_data_repository, mock_strategy_service, mock_validation_service,
    sample_price_data, backtest_request, mock_backtest_stats
):
    engine = BacktestEngine(
        data_repository=mock_data_repository,
        strategy_service_instance=mock_strategy_service,
        validation_service_instance=mock_validation_service
    )
    mock_data_repository.get_stock_data.return_value = sample_price_data

    with patch('app.services.backtest_engine.currency_converter') as mock_converter:
        mock_converter.convert_dataframe_to_usd = AsyncMock(return_value=sample_price_data)
        with patch.object(engine, '_execute_backtest', return_value=mock_backtest_stats):
            # BacktestEngine.run_backtest는 async 함수이므로 await를 사용해야 합니다.
            result = await engine.run_backtest(backtest_request)

    assert isinstance(result, BacktestResult)
    assert result.total_return_pct == 25.5
```

-   `@pytest.mark.asyncio`: 이 마커는 `pytest-asyncio`에게 해당 테스트가 비동기임을 명시적으로 알려줍니다. `strict` 모드에서는 모든 `async def` 테스트에 이 마커를 붙이는 것이 권장됩니다.

## 비동기 API 엔드포인트 테스트

`conftest.py`는 `httpx.AsyncClient` 기반의 `client`라는 이름의 픽스처를 정의합니다 (`async_client`가 아닙니다). **다만 현재 이 픽스처를 실제로 쓰는 테스트는 없습니다.** `tests/integration/test_backtest_api.py`와 `tests/unit/test_portfolio_backtest_error_contract.py`는 대신 파일 상단에서 `fastapi.testclient.TestClient(app)`(동기)를 직접 생성해 사용합니다 — API 엔드포인트 테스트는 관례상 동기 방식입니다.

### `client` 픽스처 (conftest.py, 실제 정의)

```python
# tests/conftest.py
@pytest.fixture
async def client() -> AsyncGenerator:
    """테스트용 HTTP 클라이언트 - Integration tests only"""
    if not HAS_HTTPX:
        pytest.skip("httpx not installed")
    if app is None:
        pytest.skip("FastAPI app not available")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
```

### 실제 API 테스트는 동기 `TestClient`를 사용합니다

```python
# tests/integration/test_backtest_api.py (실제 코드 발췌)
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)  # 모듈 레벨, pytest 픽스처가 아님

class TestBacktestEndpoint:
    @pytest.mark.integration
    def test_single_asset_backtest_success(self):
        payload = {
            "portfolio": [{"symbol": "AAPL", "amount": 10000.0,
                            "investment_type": "lump_sum", "asset_type": "stock"}],
            "start_date": "2023-01-01",
            "end_date": "2023-06-30",
            "strategy": "buy_hold_strategy",
            "commission": 0.002,
            "rebalance_frequency": "monthly_1"
        }

        # 실제 백테스트 API는 이 하나뿐입니다: POST /api/v1/backtest
        # (POST /api/v1/portfolio/backtest 라는 경로는 존재하지 않습니다)
        response = client.post("/api/v1/backtest", json=payload)

        assert response.status_code == 200
        assert response.json()["status"] == "success"
```

`tests/e2e/test_golden_master.py`도 같은 패턴(동기 `TestClient`)을 씁니다. `tests/e2e/test_portfolio_api.py`라는 파일은 없습니다.

## 주의사항

-   **`asyncio.to_thread`와 레이스 컨디션**: 개발 중 동기 I/O 함수를 비동기 컨텍스트에서 직접 호출하면 레이스 컨디션이 발생할 수 있습니다. 모든 동기 I/O는 `asyncio.to_thread`로 감싸야 하며, 통합 테스트를 통해 이러한 문제가 없는지 검증하는 것이 중요합니다.
-   **모킹(Mocking)**: `unittest.mock`의 `AsyncMock`을 사용하여 비동기 의존성을 모킹할 수 있습니다. 이는 외부 API 호출과 같이 제어하기 어려운 비동기 작업을 모킹할 때 유용합니다.
