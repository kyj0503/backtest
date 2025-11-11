# 테스트 실행 및 환경

이 문서는 `pytest`를 사용하여 프로젝트의 테스트를 실행하고 관리하는 방법을 안내합니다.

## 테스트 실행

모든 테스트는 프로젝트의 루트 디렉토리(`backtest_be_fast/`)에서 `pytest` 명령어를 통해 실행할 수 있습니다.

### 전체 테스트 실행

```bash
pytest
```

이 명령어는 `tests/` 디렉토리 아래의 모든 테스트 파일(`test_*.py`)을 찾아 실행합니다.

### 특정 테스트 실행

#### 마커(Marker)를 이용한 실행

테스트는 `@pytest.mark.<marker_name>` 데코레이터를 사용하여 그룹화할 수 있습니다. 이를 통해 특정 유형의 테스트만 선택적으로 실행할 수 있습니다.

-   **단위 테스트만 실행:**
    ```bash
    pytest -m unit
    ```

-   **통합 테스트만 실행:**
    ```bash
    pytest -m integration
    ```

-   **E2E 테스트만 실행:**
    ```bash
    pytest -m e2e
    ```

-   **특정 마커를 제외하고 실행:**
    ```bash
    pytest -m "not e2e"
    ```

`pytest.ini` 파일에 등록된 마커 목록은 다음과 같습니다.
```ini
[pytest]
markers =
    unit: marks tests as unit tests
    integration: marks tests as integration tests
    e2e: marks tests as end-to-end tests
    db: marks tests that require database access
```

#### 파일 또는 디렉토리 지정 실행

특정 파일이나 디렉토리 경로를 지정하여 해당 범위의 테스트만 실행할 수 있습니다.

```bash
# 특정 파일의 모든 테스트 실행
pytest tests/unit/services/test_backtest_engine.py

# 특정 디렉토리의 모든 테스트 실행
pytest tests/integration/api/

# 특정 테스트 함수 실행 (:: 사용)
pytest tests/unit/strategies/test_sma_strategy.py::test_sma_strategy_buy_signal
```

### 상세 결과 출력

`-v` (verbose) 옵션을 추가하면 각 테스트의 결과를 더 상세하게 볼 수 있습니다.

```bash
pytest -m unit -v
```

## 테스트 환경

-   **의존성**: 테스트에 필요한 라이브러리는 `requirements-test.txt` 파일에 정의되어 있습니다.
-   **설정**: 테스트 실행 시, `app/core/config.py`는 테스트 환경을 위한 설정을 로드합니다. 예를 들어, 실제 데이터베이스 대신 인메모리 데이터베이스를 사용하도록 구성할 수 있습니다.
-   **`conftest.py`**: `tests/conftest.py` 파일은 모든 테스트에서 공유하는 픽스처(fixture)와 훅(hook)을 정의하는 특별한 파일입니다. 테스트 실행 시 `pytest`가 이 파일을 자동으로 인식하고 설정합니다.
