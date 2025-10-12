# 백엔드 테스트 가이드

## 테스트 실행

**로컬:**
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -v
```

**커버리지:**
```bash
PYTHONPATH=. pytest --cov=app --cov-report=term-missing
```

**Docker:**
```bash
docker compose -f compose.dev.yaml up -d mysql redis
docker compose -f compose.dev.yaml run --rm backtest_be_fast pytest -v
```

## 테스트 마커

- `@pytest.mark.unit`: 단위 테스트
- `@pytest.mark.integration`: 통합 테스트

**마커별 실행:**
```bash
pytest -m unit -v
pytest -m integration -v
```
