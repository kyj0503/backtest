# FastAPI 백테스팅 백엔드 (backtest_be_fast)

백테스팅 기능을 담당하는 FastAPI 기반 백엔드 서비스입니다.

## 빠른 시작

```bash
# 로컬 단독 실행
python run_server.py

# Docker Compose (전체 스택)
docker compose -f compose.yml -f compose/compose.dev.yml up --build
```

## 주요 엔드포인트

- 헬스체크: `GET /health`
- API 문서: `GET /api/v1/docs`
- 백테스팅: `POST /api/v1/backtest/run`

## 테스트

### 테스트 실행

```bash
# 가상환경 설정 (최초 1회)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt requirements-test.txt

# 단위 테스트 실행
PYTHONPATH=. pytest tests/unit/ -v

# 커버리지 확인
PYTHONPATH=. pytest tests/unit/ --cov=app --cov-report=term
```

### 테스트 현황

- **단위 테스트**: 53개 (100% 통과)
  - AssetEntity: 31개 테스트, 99% 커버리지
  - PortfolioEntity: 22개 테스트, 97% 커버리지
- **통합 테스트**: 작업 예정
- **E2E 테스트**: 작업 예정

자세한 내용은 [테스트 가이드](./docs/06-Testing.md)를 참조하세요.
