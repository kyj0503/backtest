## 목표
이 저장소에서 AI 코딩 에이전트가 빠르게 생산적으로 작업하기 위한 간단·구체적 가이드. 핵심 아키텍처, 실행/디버그 명령, 프로젝트 고유 패턴, 그리고 코드 예시를 포함.

## 빠른 개요 (한 줄)
백엔드는 FastAPI(포트 8001, `backend/`), 프론트엔드는 Vite 기반 React(개발: 5174, 프로덕션: 8082), 전략은 `backend/app/services/strategy_service.py`에 등록된 Strategy 클래스들을 사용해 `backtesting` 라이브러리로 실행.

## 주요 위치
  - `backend/app/utils/data_fetcher.py`는 yfinance를 사용합니다. yfinance 관련 API 및 DB 캐시 동작의 상세 설명은 `backend/doc/api.md`를 참조. 캐시 경로·유효기간 변경은 `app/core/config.py`를 참조.

## 아키텍처·데이터 흐름 (요지)

## 프로젝트-특화 규칙 / 패턴 (에이전트가 알아야 할 것)
  - 코드를 수정하면 항상 마크다운 문서에 최신화를 해야 한다.
  - 모든 마크다운 문서들은 디렉터리 계층 구조에 맞게 작성되어야 한다.
  - 백엔드 문서는 `backend/doc/`에, 프론트엔드 문서는 `frontend/doc/`에, 전체 프로젝트 문서는 `doc/`에 위치한다.

## 실행, 빌드, 테스트 — 핵심 명령
  - 개발 환경은 윈도우, powershell, 도커 데스크탑을 사용한다.
  - `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`로 프로젝트를 실행한다.

## 빈번한 코드 변경 포인트(PR 시 체크리스트)
  - `backend/app/services/strategy_service.py`에 Strategy 클래스와 `_strategies` 엔트리 추가
  - `parameters` 메타데이터(타입, default, min, max) 정의
  - 만약 외부 의존 라이브러리가 필요하면 `backend/requirements.txt`에 추가
  - `backend/app/utils/data_fetcher.py`는 yfinance를 사용. 외부 API 키 불필요. 캐시 경로·유효기간 변경은 `app/core/config.py` 참조
  - 새 API는 `backend/app/api/v1/endpoints/`에 추가. Response/Request 모델은 `backend/app/models/`에 추가/확장
  - 프론트엔드 개선 시 우선순위: Services 계층 분리 → 유틸리티 함수 모듈화 → 커스텀 훅 도입 → 상수 모듈화 → 레거시 정리

## 예시 스니펫(에이전트가 자주 사용할 것)
  - key: 'sma_crossover'
  - class: SMAStrategy (서브클래스는 backtesting.Strategy를 상속)
  - parameters: { 'short_window': {type:'int', default:10, min:5, max:50}, 'long_window': {...} }

## 외부 의존성 및 통합 포인트

## 제한 사항 / 주의점 (현 코드에서 관찰된 것)

## To-Do

1. 핵심(High)
   - [ ] 실패 케이스 대응: yfinance가 빈 결과를 반환할 때 사용자에게 명확한 HTTP 에러(예: 404/422)와 로그를 제공하도록 백엔드를 개선합니다.
   - [ ] 회원 가입 기능
   - [ ] 내 포트폴리오 저장 기능
   - [ ] 특정 기간 동안, 또는 전체 기간 동안의 전체 자산 변동 폭, 투자 수익률을 보여주는 기능.
   - [ ] CI/CD 구축. 일단 홈서버 사용하는걸로
   - [ ] openai api를 사용해 투자자의 투자 성향에 따라서 포트폴리오의 적합성을 판단해주기.
   - [ ] 급등 또는 급락 시 뉴스 모달 띄우기
   - [ ] 사용자가 설정한 기간 동안의 다른 자산의 변동폭 보여주기(슨피나 금, 비트코인 등)
   - [ ] 단위/통합 테스트 구현

2. 개선(Medium)
   - [ ] 동시성 보호: `load_ticker_data`/`save_ticker_data`에 간단한 프로세스 내 락 또는 DB 기반 세마포어를 도입해 중복 fetch를 방지합니다.
   - [ ] 백그라운드 보충(fetch-and-upsert): 대량 또는 느린 fetch 작업은 API 호출에서 동기적으로 처리하지 말고 작업 큐(예: Redis+RQ/Celery)로 비동기화 고려.
   - [ ] yfinance 재시도 정책 개선: 휴일/주말/딜리스트 등 경계 케이스를 더 잘 처리하도록 달력/마켓 휴일 인식 로직 추가.
   - [ ] 커뮤니티 기능 추가. 수익률 비틱할 수 있게.
   - [ ] 로그인해야 백테스팅 결과를 이미지나 PDF로 저장할 수 있는 기능을 추가.
   - [ ] **프론트엔드 구조 개선(우선순위 높음)**: API 계층 분리 (`frontend/src/services/api.ts`), 유틸리티 함수 모듈화 (`frontend/src/utils/formatters.ts`), 커스텀 훅 도입 (`frontend/src/hooks/useBacktest.ts`), 전략 설정 상수화 (`frontend/src/constants/strategies.ts`)
   - [ ] **프론트엔드 레거시 정리**: `App_old.tsx`, `BacktestForm.tsx`, `PortfolioForm.tsx`, `PortfolioResults.tsx` 등 사용되지 않는 컴포넌트 제거
   - [ ] **폼 상태 관리 개선**: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer 또는 상태 라이브러리로 리팩토링
   - [ ] **에러 바운더리 추가**: React Error Boundary로 예상치 못한 컴포넌트 에러 처리

3. 장기(Low)
   - [ ] Alembic 도입 또는 문서에서 완전 제거: DB 스키마 변경이 빈번하다면 Alembic 마이그레이션을 추가합니다.
   - [ ] 로깅/모니터링: 데이터 백필/백테스트 실패 추적을 위한 Sentry/Prometheus 연동.
   - [ ] 추천하는 유튜브 컨텐츠 보여주기. 슈카월드나 오선, 미과장 같은거.
   - [ ] **전역 상태 관리 도입**: Zustand 또는 Redux로 앱 전체 상태 관리 체계 구축
   - [ ] **성능 최적화**: React.memo, useMemo, useCallback을 활용한 불필요한 리렌더링 방지
   - [ ] **프론트엔드 테스트 코드 추가**: Jest + React Testing Library로 컴포넌트 및 훅 테스트 구현
   - [ ] **로딩 상태 통합 관리**: 전역 로딩 상태 관리 및 스켈레톤 UI 도입
   - [ ] **다국어 지원(i18n)**: react-i18next를 활용한 한국어/영어 지원