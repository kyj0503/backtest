# API 가이드 (2025-09 기준)

이 문서는 `backend/app/api/v1`의 실제 구현을 기준으로 주요 REST/WS 엔드포인트를 정리합니다. 모든 예시는 Docker 개발 환경(`http://localhost:8001`)을 기준으로 합니다.

## 공통 정보

- **베이스 URL**: `http://localhost:8001/api/v1`
- **인증 헤더**: `Authorization: Bearer <세션 토큰>` (필요한 엔드포인트에만)
- **문서**: `/api/v1/docs` (Swagger), `/api/v1/redoc`

## 인증 (`/auth`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| POST | `/auth/register` | 회원가입 및 자동 로그인 |
| POST | `/auth/login` | 이메일/비밀번호 로그인 |
| POST | `/auth/logout` | 세션 토큰 폐기 |
| GET | `/auth/me` | 현재 사용자 정보 조회 |

### 회원가입/로그인 요청

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "backtest-user",
  "email": "user@example.com",
  "password": "pass1234",
  "investment_type": "balanced"
}
```

### 응답 (`AuthResponse`)

```json
{
  "token": "<세션 토큰>",
  "user_id": 1,
  "username": "backtest-user",
  "email": "user@example.com",
  "investment_type": "balanced",
  "is_admin": false
}
```

세션 토큰은 `user_sessions.token`에 저장되며 기본 만료는 7일입니다. `/auth/me`는 동일한 사용자 메타데이터를 반환합니다.

## 백테스트 (`/backtest`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| POST | `/backtest/run` | 단일 종목 백테스트 (`BacktestResult` 반환) |
| POST | `/backtest/portfolio` | 포트폴리오 백테스트 (딕셔너리 응답) |
| POST | `/backtest/execute` | 통합 백테스트 (단일/포트폴리오 자동 판별) |
| POST | `/backtest/chart-data` | Recharts용 차트 데이터 (`ChartDataResponse`) |
| GET | `/backtest/metrics` | 이벤트 시스템 메트릭 요약 |
| GET | `/backtest/notifications` | 백테스트 알림 목록 |
| GET | `/backtest/portfolio-analytics` | 포트폴리오 분석 통계 |
| GET | `/backtest/portfolio-alerts` | 포트폴리오 경고/알림 |
| GET | `/backtest/history` | 로그인 사용자의 백테스트 히스토리 |
| GET | `/backtest/history/{id}` | 히스토리 상세 |
| DELETE | `/backtest/history/{id}` | 히스토리 논리 삭제 |
| GET | `/backtest/stock-volatility-news/{ticker}` | 급등락 뉴스 + yfinance 데이터 |
| GET | `/backtest/exchange-rate` | 원/달러 환율 시계열 |

`/backtest/history*`와 `/backtest/portfolio-*` 엔드포인트는 세션 토큰 인증이 필요합니다.

### 단일 종목 백테스트 (`/backtest/run`)

```http
POST /api/v1/backtest/run
Content-Type: application/json

{
  "ticker": "AAPL",
  "start_date": "2023-01-01",
  "end_date": "2023-12-31",
  "initial_cash": 10000,
  "strategy": "buy_and_hold"
}
```

응답은 `BacktestResult` 모델(`backend/app/models/responses.py`)이며 총 수익률, 샤프 비율, 거래 통계 등 약 25개 필드를 포함합니다.

### 통합 백테스트 (`/backtest/execute`)

요청 페이로드는 `UnifiedBacktestRequest`를 따르며 단일 종목 또는 다중 종목 포트폴리오를 전송할 수 있습니다. 응답은 포트폴리오의 경우 메트릭·차트·거래 내역을 포함하는 딕셔너리이고, 단일 종목일 경우 `BacktestResult`와 동일한 구조입니다. 프론트엔드는 이 응답을 `BacktestResults.tsx`에서 소비합니다.

### 이벤트 API

- `/metrics`, `/notifications`, `/portfolio-analytics`, `/portfolio-alerts`는 메모리 내 이벤트 버퍼(`events/event_system.py`)에서 집계된 JSON을 그대로 반환합니다.
- 응답 필드는 코드와 동일한 키(`total_backtests`, `alerts`, `popular_assets` 등)를 사용합니다. 필요한 필드는 Swagger 문서를 참고하세요.

### 차트 데이터

`/backtest/chart-data`는 차트용 시계열과 거래 지표를 포함한 구조화된 데이터를 반환합니다. 모델은 `ChartDataResponse`를 참고합니다.

## 전략 (`/strategies`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/strategies` | 사용 가능한 전략 목록 (`StrategyListResponse`) |

응답은 전략 이름, 설명, 파라미터 메타데이터를 포함합니다. 프론트엔드 `constants/strategies.ts`와 동기화되어야 합니다.

## 최적화 (`/optimize`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| POST | `/optimize/run` | 전략 파라미터 최적화 (`OptimizationResult` 반환) |
| GET | `/optimize/targets` | 최적화 가능 지표 목록 |

`OptimizationRequest`는 ticker, 날짜 범위, 전략, `param_ranges`(예: `{ "short_window": [5, 20] }`), `method`(`grid` 또는 `sambo`) 등을 포함합니다. 응답에는 최적 파라미터와 해당 백테스트 결과가 포함됩니다.

## 데이터 캐시 (`/yfinance-cache`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| POST | `/yfinance-cache/fetch-and-cache` | 지정 기간의 yfinance 데이터를 강제로 가져와 DB에 저장 |

`start`, `end`(YYYY-MM-DD) 파라미터가 필요하며, 내부적으로 `data_fetcher.get_stock_data(..., use_cache=False)`를 호출합니다.

## 커뮤니티 (`/community`)

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| GET | `/community/posts` | 게시글 목록 |
| POST | `/community/posts` | 게시글 작성 (인증 필요) |
| GET | `/community/posts/{post_id}` | 게시글 상세 + 댓글 |
| POST | `/community/posts/{post_id}/comments` | 댓글 작성 (인증 필요) |
| POST | `/community/posts/{post_id}/like` | 좋아요 토글 (인증 필요) |
| POST | `/community/reports` | 신고 생성 (인증 필요) |

모든 쓰기 작업은 `Authorization` 헤더가 필요합니다. 응답은 SQLAlchemy `mappings()` 결과(dict)이며 Swagger 예제를 참고하세요.

## 채팅 (`/chat`)

- `GET /chat/rooms`: 현재 활성 채팅방 목록
- `WebSocket /chat/ws/{room}`: Redis pub/sub 기반 실시간 채팅. 연결 시 `Authorization` 헤더를 전달하면 사용자명으로 메시지가 브로드캐스트됩니다.

## 뉴스 (`/naver-news`)

네이버 뉴스 OpenAPI를 래핑한 엔드포인트가 다수 존재합니다. 주요 규칙은 다음과 같습니다.

- 기본 검색: `/naver-news/search?query=삼성전자&display=20` (`display` 1-100)
- 날짜 범위 검색: `/naver-news/search-by-date` (`display` 하한 10)
- 응답은 필터링된 기사 배열과 메타 정보를 포함합니다.
- NAVER API 키를 `.env`에 설정해야 정상 응답이 반환됩니다.

## 에러 처리

공통 에러 응답은 `ErrorResponse` 모델을 기준으로 하며, `error`, `message`, `detail`, `timestamp` 필드를 포함합니다. yfinance 오류는 `utils/user_messages.py`의 사용자 친화 메시지로 매핑됩니다.

## 테스트 및 참고

- 전체 엔드포인트 스펙은 `backend/app/api/v1/api.py`와 각 엔드포인트 모듈을 확인하세요.
- 변경 시 Swagger 문서(`/api/v1/docs`)를 통해 실제 응답과 비교하고, 필요하면 Pydantic 모델을 먼저 업데이트하십시오.
