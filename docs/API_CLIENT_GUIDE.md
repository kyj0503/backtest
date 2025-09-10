# API 연동 가이드 (클라이언트 관점)

목적: 프론트엔드가 백엔드 API와 상호작용하는 방식을 일관성 있게 유지합니다. 실제 기능과 계획만 요약하며 코드 예제는 포함하지 않습니다.

## 베이스 URL 전략
- 개발: 상대 경로(`/api`)를 사용하고 Vite 프록시가 백엔드로 라우팅합니다.
- 프로덕션: 환경변수 `VITE_API_BASE_URL` 값이 우선하며, 없으면 동일 도메인의 `/api`를 사용합니다.

## 주요 엔드포인트 (v1)
- 백테스트 실행: `POST /api/v1/backtest/run` — 단일 종목 백테스트 실행 및 요약 결과 반환.
- 차트 데이터: `POST /api/v1/backtest/chart-data` — OHLC, 자산 곡선, 거래 마커, 지표, 요약 지표 반환.
- 포트폴리오 백테스트: `POST /api/v1/backtest/portfolio` — 여러 종목과 리밸런싱 옵션 지원.
- 전략: `GET /api/v1/strategies/*` — 전략 목록 및 파라미터 메타 정보.
- 최적화: `GET /api/v1/optimize/*` — 포트폴리오 최적화 관련 리소스(확장 중).
- 데이터 캐시: `POST /api/v1/yfinance/fetch-and-cache` — yfinance 데이터를 DB에 적재/보강.
- 뉴스: `GET /api/v1/naver-news/*` — 종목/기간 기반 뉴스 조회.
-- 인증: `POST /api/v1/auth/register|login|logout` — 토큰 기반 인증 (등록 시 `investment_type` 선택 가능, 세션에 클라이언트 User-Agent/IP가 저장됨). 추가로 `GET /api/v1/auth/me`로 현재 사용자 정보를 조회할 수 있습니다.
-- 커뮤니티: `GET/POST /api/v1/community/*` — 게시글/댓글 CRUD, 좋아요/언라이크(`POST /community/posts/{id}/like`), 신고 기능(`POST /community/posts/{id}/report`) 및 공지사항(`GET /community/notices`) 지원(영구 저장소/DB 기반).
- 채팅: `WS /api/v1/chat/ws/{room}` — 실시간 채팅(WebSocket).
- 헬스체크: `GET /health` — 서버 상태 확인.
 - 헬스체크: `GET /health` — 서버 상태 확인.
 - 백테스트 히스토리: `GET /api/v1/backtest/history` — 인증된 사용자의 백테스트 실행 기록 조회. `POST /api/v1/backtest/run`는 인증 토큰이 포함되면 자동으로 히스토리에 저장합니다.
 - 관리자 API: `/api/v1/admin/*` — 공지사항 관리, 신고 처리, 사용자 관리 및 통계 대시보드 엔드포인트.

## 데이터 정책
- 소스 우선순위: DB 캐시 우선, 부재 구간은 yfinance로 보강 후 upsert.
- 현금 자산: 자산 곡선에 변동 없음(0%), 포트폴리오 합산 시 완충 역할.
- 응답 구조: 차트/요약 지표는 프론트 차트와 카드 UI에 바로 매핑되도록 평탄한 구조로 제공.

## 에러/검증
- 유효성 오류는 422를 사용하고, 존재하지 않는 티커/데이터 부재는 404로 명확히 구분합니다.
- 사용자 친화 메시지를 포함하고, 내부 로그에는 오류 ID를 첨부합니다.

## 향후 계획
- 계약 기반 스키마: 응답 필드 명세를 고정하고 파생/옵션 필드는 버전 태그로 구분.
- 배치/비동기: 장시간 백테스트를 잡 단위로 실행하고 진행률/결과 조회 API 추가.
