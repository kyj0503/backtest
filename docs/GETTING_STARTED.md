# 백테스팅 프로젝트 개발 가이드

프로젝트를 빠르게 이해하고 실행하기 위한 핵심 가이드입니다.

## 개요

- 백엔드: FastAPI (포트 8001)
- 프론트엔드: React + Vite (개발 5174, 프로덕션 8082)
- 전략 실행: `backtesting` 라이브러리, 전략 등록은 `backend/app/services/strategy_service.py`

## 실행 방법 (Docker Compose)

```bash
# 개발 환경 시작
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 백그라운드 실행 / 중지
docker compose -f compose.yml -f compose/compose.dev.yml up -d
docker compose -f compose.yml -f compose/compose.dev.yml down

# 백엔드 테스트 (컨테이너 내부)
docker compose exec backend pytest tests/ -v
```

접속 정보
- 프론트엔드: http://localhost:5174
- 백엔드: http://localhost:8001
- OpenAPI: http://localhost:8001/api/v1/docs

## 데이터/도메인 흐름

- 데이터 수집: yfinance → (옵션) MySQL 캐시 → 백테스트 엔진
- 자산 구분: 주식(symbol 기반)과 현금(asset_type='cash')
- 뉴스: 네이버 검색 API 연동(선택)

## API 엔드포인트 (요약)
- POST `/api/v1/backtest/run` (단일 종목)
- POST `/api/v1/backtest/chart-data` (차트/지표)
- POST `/api/v1/backtest/portfolio` (포트폴리오)
- GET `/api/v1/strategies/*`, `/api/v1/optimize/*`, `/api/v1/naver-news/*`

## 문서 모음

- 인덱스: `docs/README.md`
- 테스트 아키텍처(오프라인 모킹): `docs/TEST_ARCHITECTURE.md`
- DDD 개요: `docs/DDD_ARCHITECTURE.md`
- 현금 자산 처리: `docs/CASH_ASSETS.md`
- 프론트 상태/컴포넌트: `docs/STATE_MANAGEMENT.md`, `docs/COMPONENTS.md`

## 개발 참고

- 실시간 개발: 볼륨 마운트로 로컬 변경 즉시 반영
- 재빌드: 의존성 변경 시 `--build`
- CI: Jenkins 파이프라인(테스트 → 이미지 빌드/푸시 → 배포 → 통합 점검)

