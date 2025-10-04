# 테스트 안내

pytest로 단위/통합/E2E 테스트를 실행한다. 마커는 `unit`, `integration`, `e2e`를 사용한다.

로컬(단위 테스트)
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -m unit -v
```

전체 실행
```bash
cd backtest_be_fast
PYTHONPATH=. pytest -v
```

커버리지
```bash
PYTHONPATH=. pytest -m unit --cov=app --cov-report=term-missing
```

Compose(의존 서비스 필요 시)
```bash
docker compose -f compose.dev.yaml up -d mysql redis
docker compose -f compose.dev.yaml run --rm backtest_be_fast pytest -v
```

CI에서는 `pytest -v`와 커버리지 보고를 권장한다.
