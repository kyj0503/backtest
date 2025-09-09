# 프론트엔드 개발 가이드

본 문서는 `frontend/` 애플리케이션의 구조, 사용 기술, 빌드/실행 방법, 페이지/기능 구성, 그리고 백엔드 API 연동 방식을 정리합니다.

## 개요
- 프레임워크: React 18, TypeScript
- 번들러/개발서버: Vite 4
- 스타일: Tailwind CSS
- 라우팅: React Router v6
- 차트: Recharts
- 테스트: Vitest, Testing Library
- 아이콘: react-icons

## 디렉터리 구조
```
frontend/
  index.html
  package.json
  vite.config.ts            # Vite 설정 (개발 프록시 포함)
  vitest.config.ts          # 테스트 설정
  tailwind.config.js        # Tailwind 설정
  tsconfig*.json
  src/
    main.tsx                # 진입점
    App.tsx                 # 라우팅 구성
    index.css               # Tailwind 엔트리
    pages/                  # 페이지 컴포넌트 (라우트 단위)
    components/             # UI, 차트, 폼 등 재사용 컴포넌트
    components/results/     # 백테스트 결과 섹션
    components/common/      # 공용 UI (모달, 스피너 등)
    components/volatility/  # 변동성/뉴스 UI
    contexts/               # 컨텍스트 (BacktestContext 등)
    hooks/                  # 커스텀 훅 (데이터 페칭/상태)
    reducers/               # 리듀서 (폼 상태 등)
    services/               # API 클라이언트 (auth/community/backtest)
    constants/              # 전략/리밸런싱/유효성 규칙
    types/                  # 타입 정의 (API, 결과, 뉴스 등)
    utils/                  # 포맷터/숫자/날짜/차트 유틸
    test/                   # 테스트 셋업
```

## 사용 라이브러리 및 빌드 도구
- React, TypeScript: 함수형 컴포넌트, 커스텀 훅 패턴
- Vite: 빠른 HMR, 개발 프록시(`vite.config.ts` → `/api`를 백엔드로 프록시)
  - `API_PROXY_TARGET` 환경변수로 프록시 대상 제어 (기본 `http://localhost:8001`)
- Tailwind CSS: 유틸리티 퍼스트 CSS
- Recharts: 라인/에어리어/컴포지트/스캐터 차트
- Vitest + Testing Library: 단위/스냅샷/상호작용 테스트

## 환경변수
- `VITE_API_BASE_URL`: 배포 시 API 베이스 URL 설정 (미설정 시 상대 경로 `/api` 사용 → Vite 프록시)

## 실행/빌드/테스트
- 개발 서버: `cd frontend && npm ci && npm run dev` (http://localhost:5174)
- 타입 체크: `npm run type-check`
- 린트: `npm run lint`
- 테스트: `npm run test:run` (커버리지 `npm run test:coverage`)
- 도커(개발): `Dockerfile.dev` (Vite), 배포용: `Dockerfile` (Nginx)

## 라우팅과 페이지 구성
- `/` HomePage: 기능 소개, CTA. 주요 기능 카드(전략/포트폴리오/뉴스·환율), 사용 가이드 스텝 제공.
- `/backtest` BacktestPage: 통합 백테스트 폼 + 결과 뷰
  - 폼: `UnifiedBacktestForm`
    - 포트폴리오 구성(종목/현금, 투자방식, 금액, DCA 기간), 기간, 전략 선택(SMA/RSI/Bollinger/MACD/Buy&Hold), 수수료, 리밸런싱 주기
  - 실행: `useBacktest` 훅이 API 호출 → 결과 상태/에러 관리
  - 결과: `UnifiedBacktestResults`
    - 헤더: 선택 종목/기간/타입 표시
    - 차트 섹션: 전략/OHLC/거래/수익률 곡선 등 (단일) 또는 포트폴리오 수익률/개별종목 주가/성과지표
    - 추가 기능: 원·달러 환율, 변동성 이벤트별 뉴스
- `/login`, `/signup`: 토큰 기반 로그인/회원가입 폼. 성공 시 토큰과 사용자 정보 로컬스토리지 저장.
- `/community`: 게시글 목록/작성 (로그인 필요). 상세는 `/community/:id`에서 댓글 조회/작성.
- `/chat`: WebSocket 채팅(로그인 필요). 토큰을 쿼리로 전달하여 입장.

## 핵심 컴포넌트와 그래프
- 통합 폼 `components/UnifiedBacktestForm`
  - 하위: `PortfolioForm`, `DateRangeForm`, `StrategyForm`, `CommissionForm`
  - 상태: `hooks/useBacktestForm`, `reducers/backtestFormReducer`, `hooks/useFormValidation`
- 결과 뷰 `components/UnifiedBacktestResults`
  - 헤더: `results/ResultsHeader`
  - 차트 섹션: `results/ChartsSection`
    - 단일 종목
      - `OHLCChart`: 컴포지트(캔들 대체 라인+볼륨) + 보조지표(SMA/RSI/MACD 등 오버레이), 진입/청산 ReferenceLine
      - `EquityChart`: 수익률 라인과 드로우다운 영역
      - `TradesChart`: 청산 거래 PnL 산점도
      - `StockPriceChart`: 선택 종목 주가 라인
    - 포트폴리오
      - `StatsSummary`: 총/연간 수익률, 변동성, 샤프, 최대 낙폭 등
      - `EquityChart`: 포트폴리오 가치 곡선(일자별)
      - `StockPriceChart`: 구성 종목별 주가 뷰어(이전/다음 네비)
  - 추가 기능: `AdditionalFeatures`
    - `ExchangeRateChart`: USD/KRW 환율 라인 차트
    - `StockVolatilityNews`: 일일 ±5% 이상 변동 이벤트 표 + 해당 일자 네이버 뉴스 모달

## 전략/설정 상수
- `constants/strategies.ts`
  - 전략 프리셋: `buy_and_hold`, `sma_crossover`, `rsi_strategy`, `bollinger_bands`, `macd_strategy`
  - 리밸런싱 옵션: `never`, `monthly`, `quarterly`, `yearly`
  - 투자 방식: `lump_sum`, `dca`
  - 자산 타입: `stock`, `cash` (현금은 주가/변동성 없음 처리)

## 데이터 페칭 훅과 서비스
- 공통 클라이언트: `services/api.ts` → `BacktestApiService`
  - 단일 종목 백테스트 차트: `POST /api/v1/backtest/chart-data`
  - 포트폴리오 백테스트: `POST /api/v1/backtest/portfolio`
  - 주가 조회: `GET /api/v1/backtest/stock-data/{ticker}`
  - 환율: `GET /api/v1/backtest/exchange-rate`
  - 변동성 이벤트: `GET /api/v1/backtest/stock-volatility-news/{ticker}`
  - 네이버 뉴스(모달): `GET /api/v1/naver-news/search` 또는 `/ticker/{ticker}/date`
  - 에러 분류: 404 데이터없음, 422 검증, 429 레이트리밋, 0 네트워크
- 훅
  - `useBacktest`: 실행/로딩/에러/결과 관리, 단일 vs 포트폴리오 판별
  - `useStockData`: 구성 종목 주가 일괄 조회(병렬), 현금/한글 ‘현금’ 필터
  - `useExchangeRate`: 기간 환율 조회 + 요약
  - `useVolatilityNews`: 종목별 ±5% 이벤트 집계 및 뉴스 모달 관리

## 인증/커뮤니티/채팅 연동
- 인증: `services/auth.ts`
  - `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`
  - 토큰을 로컬스토리지에 저장, 커뮤니티/채팅에서 사용
- 커뮤니티: `services/community.ts`
  - 목록/상세/작성/댓글: `/api/v1/community/...` (작성/댓글은 Bearer 토큰 필요)
- 채팅: `/api/v1/chat/ws/{room}` WebSocket (쿼리 `token=`)

## 사용자 흐름 요약(페이지별)
- Home
  - 기능 소개와 시작하기 CTA 제공
- Backtest
  - 포트폴리오 구성(종목/현금, 투자방식, 금액/DCA), 기간/전략/수수료/리밸런싱 설정 → 실행
  - 결과: 지표, OHLC/수익률/거래 차트, 구성종목 주가, 환율, 변동성 이벤트 + 뉴스
- Community
  - 게시글 목록, 상세/댓글 조회. 로그인 시 글/댓글 작성 가능
- Login/Signup
  - 이메일/비밀번호 기반 토큰 발급/저장
- Chat
  - 토큰 기반 입장, 실시간 메시지 송수신

## 테스트와 품질
- Vitest + Testing Library: 컴포넌트/훅 테스트(`*.test.ts(x)`)
- ESLint: `npm run lint`, TypeScript: `npm run type-check`
- 성능: `components/common/PerformanceMonitor`로 렌더 횟수 모니터링 지원

## 개발 팁
- API 베이스 경로는 `.env`의 `VITE_API_BASE_URL` 또는 Vite 프록시(`/api`)를 사용합니다.
- 현금 자산은 심볼 `CASH` 또는 한글 `현금`으로 취급되며 주가/뉴스 조회는 생략됩니다.
- 차트 성능을 위해 `Suspense` + Lazy 로딩(`components/lazy`)을 사용합니다.

