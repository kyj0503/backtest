# 운영 런북 (DB 캐시 vs yfinance)

프로덕션/개발 환경에서 데이터 소스와 API 베이스 URL을 일관되게 운영하기 위한 가이드입니다.

문제 발생 시: 운영 관련 트러블슈팅은 [jenkins_troubleshooting.md](./jenkins_troubleshooting.md)를 참고하세요.

## 데이터 소스 전략

- 원칙: 파일 기반 캐시는 사용하지 않습니다.
- 데이터 소스 우선순위
  1) MySQL 캐시(DB)
  2) yfinance API(부재 구간 보충 및 최초 적재)

### 구성 요소
- `app/services/yfinance_db.py`
  - `load_ticker_data(ticker, start_date, end_date)`
    - DB에 데이터가 없으면 yfinance에서 가져와 `save_ticker_data()`로 저장 후 재조회
    - DB 범위에 누락 구간이 있으면 보강 페치(+/- PAD) 후 upsert
- `app/utils/data_fetcher.py`
  - 직접 yfinance에서 데이터를 수집(파일 캐시 미사용)

### 환경 변수
- `DATABASE_URL`: SQLAlchemy 연결 문자열 사용. 운영·개발 환경에 맞는 호스트/포트/스키마를 지정합니다.

### 로컬 개발(도커)
- `compose.yml`과 `compose/compose.dev.yml`을 함께 사용합니다. 백엔드는 8001, 프론트는 5174(개발)/8082(프로덕션) 포트를 사용합니다.
- 별도 DB 사용 시 `DATABASE_URL`을 컨테이너 호스트:포트로 지정합니다.

## API 베이스 URL 전략(프론트엔드)

- 기본: 상대 경로(`/api`) 사용 → 개발 시 Vite proxy가 백엔드로 라우팅
- 환경 변수: `VITE_API_BASE_URL`가 설정된 경우 이를 우선 사용
  - 예: `VITE_API_BASE_URL=https://backtest-be.example.com`

참고: `frontend/src/services/api.ts`에서 위 전략을 구현합니다.

## 헬스체크

- `GET /health`: 외부 네트워크 호출 없이 경량 자체 점검만 수행합니다.
- OpenAPI 문서: `GET /api/v1/docs`

## 트러블슈팅

- DB 연결 불가: `DATABASE_URL` 포맷과 네트워크 접근 가능 여부 확인. 프로덕션은 DB 캐시 사용 권장.
- yfinance 레이트리밋: 테스트/CI에서는 오프라인 픽스처 사용 권장(테스트 문서 참고).

## 체크리스트
- `DATABASE_URL` 설정 확인
- (개발) Vite 프록시 타깃 확인
- (프론트) 필요 시 `VITE_API_BASE_URL` 지정
- `/api/v1/docs` 접근 확인
