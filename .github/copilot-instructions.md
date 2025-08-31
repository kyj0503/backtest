## 목표
이 저장소에서 AI 코딩 에이전트가 빠르게 생산적으로 작업하기 위한 간단·구체적 가이드. 핵심 아키텍처, 실행/디버그 명령, 프로젝트 고유 패턴, 그리고 코드 예시를 포함.

## 빠른 개요 (한 줄)
백엔드는 FastAPI(포트 8001, `backend/`), 프론트엔드는 Vite 기반 React(개발: 5174, 프로덕션: 8082), 전략은 `backend/app/services/strategy_service.py`에 등록된 Strategy 클래스들을 사용해 `backtesting` 라이브러리로 실행.

## 주요 위치
  - `backend/app/utils/data_fetcher.py`는 yfinance를 사용합니다. yfinance 관련 API 및 DB 캐시 동작의 상세 설명은 `backend/doc/api.md`를 참조. 캐시 경로·유효기간 변경은 `app/core/config.py`를 참조.

## 아키텍처·데이터 흐름 (요지)
  - **백엔드**: FastAPI + uvicorn, MySQL (캐시), yfinance (데이터 소스)
  - **프론트엔드**: React 18 + TypeScript + Vite, React Bootstrap, Recharts
  - **데이터베이스**: MySQL (`stock_data_cache`) - `host.docker.internal:3306`
  - **API 구조**: `/api/v1/backtest/chart-data` (단일 종목), `/api/v1/backtest/portfolio` (포트폴리오), `/api/v1/system/info` (시스템 정보)
  - **전략 시스템**: `backtesting` 라이브러리 기반, Strategy 클래스 상속 구조
  - **시스템 모니터링**: 프론트엔드와 백엔드 버전, 업타임, 환경 정보 표시 (푸터)

## 프로젝트-특화 규칙 / 패턴 (에이전트가 알아야 할 것)
  - 코드를 수정하면 항상 마크다운 문서에 최신화를 해야 한다.
  - 모든 마크다운 문서들은 디렉터리 계층 구조에 맞게 작성되어야 한다.
  - 백엔드 문서는 `backend/doc/`에, 프론트엔드 문서는 `frontend/doc/`에, 전체 프로젝트 문서는 `doc/`에 위치한다.

## 실행, 빌드, 테스트 — 핵심 명령
  - 개발 환경은 윈도우, powershell, 도커 데스크탑을 사용한다.
  - 프로젝트 코드는 항상 개발환경(윈도우 + powershell + 도커 컴포즈 + 도커 데스크탑 환경)과 운영환경(우분투 서버, 호스트에 설치된 젠킨스와 MySQL 서버, 도커 컴포즈 활용) 모두에서 문제없이 작동해야 해.
  - `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build`로 프로젝트를 실행한다.
  - 백그라운드 실행: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
  - 컨테이너 중지: `docker-compose -f docker-compose.yml -f docker-compose.dev.yml down`
  - 개발 서버 접근: 프론트엔드 http://localhost:5174, 백엔드 http://localhost:8001
  - **CI/CD**: 젠킨스 파이프라인은 main 브랜치 푸시 시 자동 실행됨
  - **테스트**: 백엔드 `pytest backend/tests/`, 프론트엔드 `npm test` (Docker 빌드 과정에 포함)
  - **CI/CD 테스트**: 젠킨스에서 각각 별도 스테이지로 테스트 실행, 빌드 인수와 분리

## 빈번한 코드 변경 포인트(PR 시 체크리스트)
  - `backend/app/services/strategy_service.py`에 Strategy 클래스와 `_strategies` 엔트리 추가
  - `parameters` 메타데이터(타입, default, min, max) 정의
  - 만약 외부 의존 라이브러리가 필요하면 `backend/requirements.txt`에 추가
  - `backend/app/utils/data_fetcher.py`는 yfinance를 사용. 외부 API 키 불필요. 캐시 경로·유효기간 변경은 `app/core/config.py` 참조
  - 새 API는 `backend/app/api/v1/endpoints/`에 추가. Response/Request 모델은 `backend/app/models/`에 추가/확장
  - 프론트엔드 아키텍처: Services 계층(`frontend/src/services/`), 유틸리티 함수(`frontend/src/utils/`), 커스텀 훅(`frontend/src/hooks/`), 상수 모듈(`frontend/src/constants/`) 구조로 구성됨
  - 프론트엔드 개선 시 우선순위: 폼 상태 관리 → 에러 바운더리 → 성능 최적화 → 테스트 코드
  - **시스템 정보**: 새로운 환경 변수나 버전 정보는 `backend/app/api/v1/endpoints/system.py`와 `frontend/src/components/ServerStatus.tsx`에 반영
  - **버전 추적**: Git 커밋과 빌드 번호는 Docker 빌드 시 환경 변수로 주입되어 시스템 정보에 표시됨

## 예시 스니펫(에이전트가 자주 사용할 것)
  - 5개 전략 지원: buy_and_hold, sma_crossover, rsi_strategy, bollinger_bands, macd_strategy
  - key: 'sma_crossover'
  - class: SMAStrategy (서브클래스는 backtesting.Strategy를 상속)
  - parameters: { 'short_window': {type:'int', default:10, min:5, max:50}, 'long_window': {...} }

## 외부 의존성 및 통합 포인트
  - **yfinance**: 주식 데이터 수집 (API 키 불필요)
  - **MySQL**: 데이터 캐시 저장소 (설정: `backend/.env`)
  - **backtesting**: 백테스트 엔진 라이브러리
  - **Docker**: 컨테이너화된 개발/배포 환경
  - **nginx**: 프로덕션 환경 리버스 프록시

## 제한 사항 / 주의점 (현 코드에서 관찰된 것)
  - **MySQL 연결**: 윈도우 도커 환경에서 `host.docker.internal` 사용 필수
  - **우분투 CI/CD**: 젠킨스 빌드 환경에서 MySQL `127.0.0.1` 접근 불가, 테스트에서 오프라인 모킹 시스템 사용
  - **포트 매핑**: 개발 환경에서 프론트엔드 5174:5174, 백엔드 8001:8000
  - **yfinance 제한**: 시장 휴일/주말 데이터 없음, 일일 API 제한 존재 가능
  - **캐시 의존성**: MySQL 연결 실패 시 전체 백테스트 기능 중단
  - **전략 확장**: 새 전략 추가 시 프론트엔드 상수 파일도 동기화 필요
  - **테스트 환경**: pytest(백엔드), Vitest(프론트엔드) 사용, 완전 오프라인 모킹 시스템으로 CI/CD 안정성 확보
  - **버전 추적**: Git 정보와 빌드 번호는 빌드 시점에 환경 변수로 주입되어 배포 상태 추적 가능
  - **타입스크립트 빌드**: 프론트엔드에서 사용하지 않는 변수 선언 시 빌드 실패 (strict 모드)
  - 내가 별다른 첨언 없이 로그만 입력하면, 로그를 바탕으로 문제점이나 개선점을 찾아 알려줘.

## 백엔드 테스트 아키텍처 가이드라인

### 테스트 구조 (3-Tier Architecture)
```
backend/tests/
├── unit/                   # 단위 테스트 (개별 함수/클래스)
│   ├── test_data_fetcher.py
│   ├── test_strategy_service.py
│   └── test_backtest_service.py
├── integration/            # 통합 테스트 (서비스 간 상호작용)
│   ├── test_api_endpoints.py
│   └── test_backtest_flow.py
├── e2e/                   # 종단 테스트 (전체 시나리오)
│   └── test_complete_backtest.py
├── fixtures/              # 테스트 픽스처 및 모킹 데이터
│   ├── mock_data.py
│   ├── expected_results.py
│   └── test_scenarios.json
├── conftest.py           # pytest 설정 및 글로벌 픽스처
├── pytest.ini           # pytest 설정 파일
└── requirements-test.txt # 테스트 전용 의존성
```

### 오프라인 모킹 시스템 원칙
- **완전 격리**: yfinance API, MySQL DB 등 외부 의존성 완전 제거
- **수학적 모델링**: Geometric Brownian Motion 기반 현실적 주식 데이터 생성
- **DB 스키마 준수**: stock_data_cache 테이블 구조 (DECIMAL 19,4) 완전 호환
- **시나리오 기반**: 정상/비정상/극한 상황 모든 케이스 커버
- **CI/CD 최적화**: 젠킨스 우분투 환경에서 100% 성공률 보장

### 테스트 작성 가이드라인
1. **단위 테스트**: 개별 함수의 입출력 검증, 모든 브랜치 커버
2. **통합 테스트**: 서비스 레이어 간 데이터 흐름 검증
3. **종단 테스트**: 실제 사용자 시나리오 완전 재현
4. **성능 테스트**: 대용량 데이터 처리 시간 제한 검증
5. **오류 처리**: 예외 상황 및 경계 조건 철저 테스트

### 모킹 데이터 품질 기준
- **현실성**: 실제 주식 시장 패턴 (변동성, 트렌드, 계절성) 반영
- **일관성**: 동일 시드값으로 재현 가능한 결정적 데이터
- **다양성**: 상승/하락/횡보 등 다양한 시장 상황 시뮬레이션
- **정확성**: OHLCV 데이터 논리적 일관성 (High ≥ Open, Close / Low ≤ Open, Close)

### 테스트 실행 및 CI/CD 통합
- **로컬 개발**: `pytest backend/tests/` (전체), `pytest backend/tests/unit/` (단위만)
- **Docker 환경**: `docker-compose exec backend pytest tests/ -v` (권장)
- **Jenkins CI**: 각 티어별 독립 실행으로 실패 지점 명확 식별
- **커버리지 목표**: 단위 테스트 90%+, 통합 테스트 80%+, 종단 테스트 주요 시나리오 100%
- **실행 시간**: 단위 테스트 <30초, 통합 테스트 <2분, 종단 테스트 <5분

### Docker 볼륨 마운트 주의사항
- **개발 환경**: `docker-compose.dev.yml`의 볼륨 마운트로 인해 로컬 변경사항 즉시 반영
- **테스트 파일 추가/수정 시**: 컨테이너 재빌드 필요 (`docker-compose up --build`)
- **볼륨 덮어쓰기 문제**: Dockerfile의 COPY가 런타임 볼륨 마운트로 덮어씌워질 수 있음
- **해결책**: 테스트 관련 변경 후 항상 `--build` 플래그로 재빌드

## To-Do

1. **Critical (즉시 필요)**

2. **High (비즈니스 핵심 기능)**
   - [ ] **백테스트 결과 개선**: 월별/연도별 수익률 분석, 베타 계수, 최대 연속 손실 기간 등 추가 통계 제공
   - [ ] **회원 가입 기능**: 사용자 관리 시스템 구축
   - [ ] **내 포트폴리오 저장 기능**: 사용자별 포트폴리오 관리
   - [ ] **특정 기간 동안의 전체 자산 변동 폭, 투자 수익률 분석**: 성과 분석 고도화
   - [ ] **폼 상태 관리 개선**: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer로 리팩토링

3. **Medium (사용자 경험 개선)**
   - [ ] **yfinance 재시도 정책 개선**: 휴일/주말/딜리스트 등 경계 케이스 처리
   - [ ] **동시성 보호**: `load_ticker_data`/`save_ticker_data`에 프로세스 내 락 도입해 중복 fetch 방지
   - [ ] **차트 성능 최적화**: 큰 데이터셋에 대한 가상화 및 차트 렌더링 최적화
   - [ ] **사용자가 설정한 기간 동안의 다른 자산 변동폭 비교**: 슨피500, 금, 비트코인 등 벤치마크 제공
   - [ ] **CI/CD 구축**: 홈서버 기반 자동 배포 시스템

4. **Low (고급 기능 및 확장)**
   - [ ] **openai api 포트폴리오 적합성 분석**: AI 기반 투자 성향 분석
   - [ ] **급등/급락 시 뉴스 모달**: 실시간 뉴스 연동
   - [ ] **커뮤니티 기능**: 수익률 공유 및 랭킹 시스템
   - [ ] **백그라운드 작업 큐**: Redis+RQ/Celery로 대량 데이터 처리 비동기화
   - [ ] **로그인 기반 결과 저장**: 백테스팅 결과를 이미지나 PDF로 저장
   - [ ] **프론트엔드 테스트 코드**: Jest + React Testing Library 테스트 구현

5. **Future (장기 계획)**
   - [ ] **로깅/모니터링**: Sentry/Prometheus 연동으로 운영 안정성 향상
   - [ ] **전역 상태 관리**: Zustand/Redux로 앱 전체 상태 관리
   - [ ] **성능 최적화**: React.memo, useMemo, useCallback 최적화
   - [ ] **로딩 상태 통합 관리**: 전역 로딩 상태 및 스켈레톤 UI
   - [ ] **다국어 지원(i18n)**: react-i18next 한국어/영어 지원
   - [ ] **추천 유튜브 컨텐츠**: 투자 교육 컨텐츠 큐레이션
   - [ ] **Alembic 마이그레이션**: DB 스키마 변경 관리 체계화