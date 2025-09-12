# 트러블슈팅 가이드

프로젝트 실행, 테스트, 배포 과정에서 자주 발생하는 문제와 해결 절차를 체계적으로 정리했습니다. 모든 지침은 현재 코드와 컴포즈 구성(`compose.yml`, `compose/compose.dev.yml`, `compose/compose.prod.yml`, `compose/compose.test.yml`)을 기준으로 합니다.

## 목차
- 개발 환경 구동 문제
- 컨테이너/포트 충돌
- 백엔드 헬스체크 실패
- 프론트엔드 접속 불가
- 데이터베이스/Redis 연결 문제
- yfinance 데이터 이슈
- 네이버 뉴스 API 오류
- 테스트 실행 실패
- 권한/인증 관련 오류
- 자주 묻는 질문(FAQ)

---

## 개발 환경 구동 문제

증상: `docker compose -f compose.yml -f compose/compose.dev.yml up --build` 실행 실패 또는 컨테이너 즉시 종료

확인 및 조치:
1) Docker/Compose 버전 확인
```bash
docker version

```
2) 캐시 없이 재빌드
```bash
docker compose -f compose.yml -f compose/compose.dev.yml build --no-cache
```
3) 서비스 로그 확인
```bash
docker compose -f compose.yml -f compose/compose.dev.yml logs -f backend
```

## 컨테이너/포트 충돌

증상: 포트 바인딩 실패(`8001`, `5174`, `8082` 등)

조치:
```bash
ss -ltnp | grep -E ":(8001|5174|8082)"
kill -9 <PID>
```
주의: 기본 `compose.yml`은 프런트엔드의 프로덕션 포트(8082)를 더 이상 노출하지 않습니다. 개발 스택은 `compose.yml + compose/compose.dev.yml` 병합으로 프런트엔드 5174만 노출됩니다. 필요 시 해당 오버레이에서 `ports` 매핑을 확인/수정하세요.

## 백엔드 헬스체크 실패

증상: `GET http://localhost:8001/health` 503 또는 타임아웃

조치:
- 백엔드 로그 확인
```bash
docker compose -f compose.yml -f compose/compose.dev.yml logs -f backend
```
- 환경 변수 확인: `backend/app/core/config.py` 기준(`host`, `port`, `BACKEND_CORS_ORIGINS`, `REDIS_URL` 등)
- 로컬 빠른 실행으로 재확인
```bash
cd backend
python run_server.py
```
성공 기준: 200 OK, `{ "status": "healthy" }` 응답

## 프론트엔드 접속 불가

증상: `http://localhost:5174` 접속 불가

조치:
```bash
docker compose -f compose.yml -f compose/compose.dev.yml ps
docker compose -f compose.yml -f compose/compose.dev.yml logs -f frontend
```
환경 변수 `API_PROXY_TARGET=http://backend:8000` 확인 후 재시작:
```bash
docker compose -f compose.yml -f compose/compose.dev.yml restart frontend
```

## 데이터베이스/Redis 연결 문제

증상: 통합/E2E 테스트 중 DB 또는 Redis 연결 실패

조치:
```bash
docker compose -f compose/compose.test.yml up -d
docker compose -f compose/compose.test.yml ps
```
기본 네트워크/컨테이너 이름: `test_network`, `mysql-test`, `redis-test`

필요 시 연결 정보 주입:
```bash
DATABASE_URL="mysql+pymysql://test_user:test_password@mysql-test:3306/stock_data_cache"
REDIS_URL="redis://redis-test:6379"
```

## yfinance 데이터 이슈

증상: 데이터 없음, 심볼 오류, 레이트 리밋

조치:
- 심볼 형식 확인(미국: 대문자, 한국: `.KS` 접미사 예 `005930.KS`)
- 기간 내 거래일 없음 여부 확인(휴장 포함), 범위 확대 후 재시도
- DB 캐시 우선 사용 권장, 필요 시 수동 캐시 적재
```bash
POST /api/v1/yfinance/fetch-and-cache?ticker=AAPL&start=2023-01-01&end=2023-12-31&interval=1d
```

## 네이버 뉴스 API 오류

증상: 401/403, 빈 결과

조치:
- 환경 변수 설정: `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`
- 일반 검색(`/search`, `/ticker/{ticker}`): `display` 1~100 허용
- 날짜 기반(`/search-by-date`, `/ticker/{ticker}/date`): `display` 최소 10
- 네트워크 오류는 재시도/지수 백오프 적용됨. 반복 실패 시 키/네트워크 점검

## 테스트 실행 실패

증상: `./scripts/test-runner.sh unit|integration|e2e` 실패

조치:
- 캐시 없이 이미지 재빌드
- 통합/E2E 전 `compose/compose.test.yml` 구동 확인
```bash
docker compose -f compose/compose.test.yml up -d
```
- 커버리지 실행
```bash
./scripts/test-runner.sh coverage
```

## 권한/인증 관련 오류

증상: 401/403, WebSocket 연결 실패

조치:
- `Authorization: Bearer <token>` 헤더 포함
- WebSocket: `ws://localhost:8001/api/v1/chat/ws/<room>?token=<JWT>`
- 토큰 만료 시 재로그인

## 자주 묻는 질문(FAQ)

- 포트 요약: 백엔드 8001(외부)→8000(컨테이너), 프론트엔드 5174(개발)/8082(배포)
- API 문서: `http://localhost:8001/api/v1/docs`
- 이벤트/메트릭/알림 API는 `app/events` 시스템과 통합되어 별도 설정 없이 사용 가능

## 관련 문서
- [API 가이드](./API_GUIDE.md)
- [개발 가이드](./DEVELOPMENT_GUIDE.md)
- [운영 가이드](./OPERATIONS_GUIDE.md)
- [런북](./RUNBOOK.md)
- API 키 유효성 확인
