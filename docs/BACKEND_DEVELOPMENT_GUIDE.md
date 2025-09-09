# 백엔드 개발 가이드

본 문서는 `backend/` FastAPI 애플리케이션의 구조, 도메인/서비스 계층, 주요 API 명세, 데이터 저장 구조, 에러/로그 처리, 그리고 프론트엔드에서의 활용 방식을 정리합니다.

## 개요
- 프레임워크: FastAPI
- 모델/설정: Pydantic v2, pydantic-settings
- 실행: Uvicorn
- 데이터 소스: yfinance + 내부 캐시 DB (MySQL 기반 스키마), KRW 환율
- 추가 기능: 포트폴리오 백테스트, 전략 최적화, 커뮤니티(게시글/댓글), 인증(간단 토큰), Redis WebSocket 채팅, 네이버 뉴스 검색

## 디렉터리 구조(요약)
```
backend/
  app/
    main.py                 # FastAPI 엔트리, CORS/라우터/헬스체크/전역 예외
    core/                   # 설정/예외
    api/v1/                 # 버전별 API 라우터와 엔드포인트
      api.py
      endpoints/
        backtest.py         # 백테스트/차트/포트폴리오/환율/변동성 이벤트/주가
        strategies.py       # 전략 목록/정보/파라미터 검증
        optimize.py         # 전략 파라미터 최적화
        yfinance_cache.py   # 원천 데이터 페치 후 DB 캐시 저장
        auth.py             # 회원가입/로그인/로그아웃, 토큰 검증
        community.py        # 게시글/댓글
        chat.py             # Redis PubSub WebSocket 채팅
        naver_news.py       # 네이버 뉴스 검색/티커별/기간별 검색
    models/                 # 요청/응답 스키마
    domains/                # DDD 레이어(백테스트/포트폴리오/데이터)
    services/               # 애플리케이션 서비스(백테스트/포트폴리오/전략 등)
    repositories/           # 리포지토리(데이터/백테스트)
    events/                 # 이벤트/핸들러
    strategies/             # 전략 구현체
```

## 실행/개발
- 로컬 실행: `cd backend && python run_server.py`
- 도커/컴포즈: 최상위 `compose.yml` + `compose/compose.dev.yml`
- 환경설정: `app/core/config.py` (env: `.env`) / 기본 포트 `8000` (compose 기준 8001)
- CORS: `BACKEND_CORS_ORIGINS`(쉼표구분/JSON 두 형식 모두 지원)

## 주요 의존성
- fastapi, uvicorn, pydantic, pydantic-settings
- backtesting, yfinance, matplotlib/bokeh (시각화/계산), pandas (간접 의존)
- SQLAlchemy, PyMySQL (DB 연동), redis (채팅)
- pytest, pytest-asyncio (테스트)

## 데이터베이스
- 디렉터리: `database/`
  - `yfinance.sql`: 캐시 DB 스키마 (stocks, prices, dividends 등)
  - `schema.sql`: 사용자/세션, 커뮤니티(게시글/댓글) 스키마
- 런타임 접근: `app/services/yfinance_db.py`의 `_get_engine()`을 통해 연결

## 레이어 개요
- API 레이어(`app/api/v1/endpoints/*`): 입출력 검증, 에러 매핑, 서비스 호출
- 서비스 레이어(`app/services/*`): 백테스트 실행/차트 변환/최적화/포트폴리오 계산
- 도메인 레이어(`app/domains/*`): 엔티티/밸류/도메인 서비스 (백테스트·포트폴리오·데이터)
- 리포지토리(`app/repositories/*`): 데이터 접근 추상화
- 이벤트(`app/events/*`): 백테스트/포트폴리오 이벤트 및 핸들러

## 에러/로그/헬스체크
- 전역 예외 핸들러(`main.py`): 500 시 표준 응답
- `utils/user_messages.py`: 사용자 친화 메시지 매핑 + 디버그용 에러 ID 로깅
- `/health` 및 `/api/v1/backtest/health`: 경량 점검

## API 명세(핵심)

공통 prefix: `/api/v1`

1) 백테스트/차트/보조 API (`endpoints/backtest.py`)
- POST `/backtest/run` — 단일 종목 백테스트 실행
  - Body: BacktestRequest(ticker, start_date, end_date, initial_cash, strategy, strategy_params?, commission, spread?, benchmark_ticker?)
  - 동작: DB 캐시 우선 사용 → 없으면 yfinance 조회 → 실행 후 지표/통계 반환(BacktestResult)
- POST `/backtest/chart-data` — 단일 종목 백테스트 + 차트용 데이터
  - Body: BacktestRequest (동일) → OHLC, equity, trades, indicators, summary_stats
- POST `/backtest/portfolio` — 포트폴리오 백테스트
  - Body: PortfolioBacktestRequest
    - portfolio[{ symbol, amount, investment_type(lump_sum|dca), dca_periods, asset_type(stock|cash) }]
    - start_date, end_date, commission, rebalance_frequency(never|monthly|quarterly|yearly)
  - Return: { status, data: { portfolio_statistics, equity_curve, daily_returns, portfolio_composition, ... } }
- GET `/backtest/stock-data/{ticker}?start_date&end_date` — 날짜별 종가/거래량
  - CASH/현금은 빈 배열 반환
- GET `/backtest/exchange-rate?start_date&end_date` — KRW=X 환율 시계열
- GET `/backtest/stock-volatility-news/{ticker}?start_date&end_date&threshold=5.0`
  - 일일 ±threshold 이상 변동한 날짜/수익률/가격/거래량 목록(최대 10개)

2) 전략 관리 (`endpoints/strategies.py`)
- GET `/strategies/` — 사용가능 전략 목록(이름/설명/파라미터)
- GET `/strategies/{name}` — 특정 전략 정보
- GET `/strategies/{name}/validate?param=...` — 파라미터 유효성 검증

3) 최적화 (`endpoints/optimize.py`)
- POST `/optimize/run` — 그리드/SAMBO로 파라미터 최적화(OptimizationRequest)
- GET `/optimize/targets` — 최적화 지표 목록(SQN/Sharpe 등)
- GET `/optimize/methods` — 지원 방법(grid/sambo)

4) 데이터 캐시 (`endpoints/yfinance_cache.py`)
- POST `/yfinance/fetch-and-cache?ticker&start&end&interval=1d` — yfinance 원천 → DB 저장

5) 인증/세션 (`endpoints/auth.py`)
- POST `/auth/register`, POST `/auth/login`, POST `/auth/logout`
- 내부 토큰 저장: `user_sessions` (만료 포함). 보호 엔드포인트는 `Authorization: Bearer <token>` 필요.

6) 커뮤니티 (`endpoints/community.py`)
- GET `/community/posts`, GET `/community/posts/{id}`
- POST `/community/posts`, POST `/community/posts/{id}/comments` (인증 필요)

7) 채팅 (`endpoints/chat.py`)
- WS `/chat/ws/{room}?token=...` — Redis PubSub 기반 채팅

8) 네이버 뉴스 (`endpoints/naver_news.py`)
- GET `/naver-news/search?query&display` — 단순 검색
- GET `/naver-news/ticker/{ticker}` — 티커 매핑으로 회사명 기반 검색
- GET `/naver-news/search-by-date?query&start_date&end_date&display` — 날짜 필터링 검색
- GET `/naver-news/ticker/{ticker}/date?start_date&end_date&display` — 티커 + 일자

각 엔드포인트는 실패 시 `ErrorResponse` 형태 혹은 HTTPException(detail에 사용자 메시지/오류 ID 포함)로 응답합니다.

## 요청/응답 스키마
- `models/requests.py`
  - BacktestRequest, OptimizationRequest, PlotRequest 등 (Pydantic v2 `field_validator`로 날짜 파싱/검증)
- `models/responses.py`
  - BacktestResult, OptimizationResult, ChartDataResponse 등 (예시 스키마 포함)

## 프론트엔드 연동 포인트(실사용)
- Backtest UI
  - 단일 차트: `POST /backtest/chart-data` (OHLC/자산곡선/거래/지표/요약)
  - 포트폴리오: `POST /backtest/portfolio` (구성/수익률/지표)
  - 주가 조회: `GET /backtest/stock-data/{ticker}` (구성종목 라인차트)
  - 환율: `GET /backtest/exchange-rate` (USD/KRW 차트)
  - 변동성 이벤트: `GET /backtest/stock-volatility-news/{ticker}` (±5% 일자 리스트)
- 뉴스: `GET /naver-news/...` (모달에서 해당 일자 뉴스 조회)
- 인증/커뮤니티: `/auth/*`, `/community/*` (로그인 후 글/댓글 작성)
- 채팅: `WS /chat/ws/general?token=...`

## 캐시 및 데이터 소스 전략
- yfinance 데이터는 `services/yfinance_db.py`에 의해 DB 캐시에 저장/조회(`load_ticker_data`, `save_ticker_data`)
- 백테스트 실행 시: DB 우선 → 미존재 시 yfinance로 조회 (레이트리밋/네트워크 오류 시 사용자 메시지 가공)

## 테스트
- `backend/tests/`에 단위/통합/E2E 테스트 모음
- 실행: `cd backend && pytest -q` (커버리지 옵션 참조)

## 개발 팁
- API 문서: `http://<host>:<port>/api/v1/docs`
- 예외 메시지에 포함된 “오류 ID”는 로그 상관관계용. 프론트에서 그대로 사용자에게 노출해도 무방합니다.
- 포트폴리오 요청에 현금 자산이 포함되면 항상 포트폴리오 엔드포인트를 사용합니다.
- CORS는 `.env`의 `BACKEND_CORS_ORIGINS`로 관리합니다.

