# Backtest

## 요구사항

- Docker 및 Docker Compose

## CRITICAL: 개발자 필독 사항

**레이스 컨디션 경고 - 백테스트 결과 정확성에 직접 영향**

이 프로젝트는 FastAPI(async)를 사용하지만, yfinance와 SQLAlchemy는 동기 I/O를 사용합니다. 동기 함수를 async 컨텍스트에서 직접 호출하면 레이스 컨디션이 발생하여 첫 실행 시 데이터가 손상됩니다.

**코드 작성/수정 시 필수 확인 사항:**
- async 함수 내에서 모든 I/O 호출은 `await asyncio.to_thread()`로 래핑
- 특히 `load_ticker_data()`, `get_stock_data()`, `save_ticker_data()` 호출 시 주의
- 리팩토링 시 async/sync 경계 유지 확인

**상세 내용:** `.github/copilot-instructions.md`, `CLAUDE.md`, `backtest_be_fast/docs/race_condition_reintroduced_analysis.md` 참조

## 빠른 시작 (Docker 개발 환경)

아래 명령은 프로젝트 루트에서 실행합니다. 개발용 Docker Compose 파일을 사용하여 백엔드 및 프론트엔드를 빌드하고 핫 리로드 설정으로 실행합니다.

```bash
# 개발 컨테이너 빌드 및 실행
docker compose -f compose.dev.yaml up -d --build

# 백엔드 로그 확인
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# 서비스 접근
# 프론트엔드: http://localhost:5173
# 백엔드 API: http://localhost:8000
# API 문서: http://localhost:8000/api/v1/docs
```

컨테이너를 중지하려면:

```bash
docker compose -f compose.dev.yaml down
```

## 개별 서비스

- 백엔드
  - 경로: `backtest_be_fast/`
  - 주요 명령: `run_server.py` (컨테이너 또는 로컬 Python에서 실행 가능)
  - 의존성: `requirements.txt`, 테스트용 `requirements-test.txt`

- 프론트엔드
  - 경로: `backtest_fe/`
  - 주요 명령: `npm run dev` (또는 `pnpm`/`yarn` 사용 시 각 툴의 명령)
  - 설정: Vite + React + TypeScript

## 테스트

- 백엔드: pytest를 사용합니다. 컨테이너 내부 또는 로컬 가상환경에서 실행하세요.

```bash
# 예: 로컬에서 빠르게 유닛 테스트 실행
# cd backtest_be_fast
# pytest tests/unit
```

## 환경 변수

- 프로젝트 루트의 `.env` 파일(또는 환경 변수)을 사용합니다. 백엔드와 프론트엔드 모두 개발용 환경 변수를 `compose.dev.yaml`에서 참조합니다.
