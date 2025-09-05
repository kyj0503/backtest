# 백테스팅 프로젝트 개발 가이드

이 저장소에서 AI 코딩 에이전트가 효율적으로 작업하기 위한 핵심 가이드입니다.

## 빠른 개요

백테스팅 시스템은 FastAPI 백엔드(포트 8001)와 Vite 기반 React 프론트엔드(개발: 5174, 프로덕션: 8082)로 구성됩니다. 투자 전략은 `backend/app/services/strategy_service.py`에 등록된 Strategy 클래스들을 사용해 `backtesting` 라이브러리로 실행됩니다.

## 아키텍처

### 기술 스택
- **백엔드**: FastAPI + uvicorn, Pydantic V2, MySQL 캐시, yfinance API
- **프론트엔드**: React 18 + TypeScript + Vite, Tailwind CSS, Recharts
- **배포**: Docker + Jenkins CI/CD, nginx 프록시

### 데이터 흐름
- **데이터 수집**: yfinance → MySQL 캐시 → 백테스트 엔진
- **뉴스 검색**: 네이버 검색 API → 70+ 종목 지원, 날짜별 필터링
- **자산 관리**: 주식(ticker 기반)과 현금(asset_type='cash') 구분 처리
- **현금 자산**: 무위험 자산으로 0% 수익률, 변동성 없음 보장

### API 구조
- `/api/v1/backtest/run` - 단일 종목 백테스트
- `/api/v1/backtest/chart-data` - 백테스트 차트 데이터
- `/api/v1/backtest/portfolio` - 포트폴리오 백테스트
- `/api/v1/naver-news/*` - 뉴스 검색
- `/api/v1/strategies/*` - 전략 관리
- `/api/v1/optimize/*` - 최적화
- `/api/v1/yfinance/*` - yfinance 캐시

## 개발 환경

### 실행 명령어
```bash
# 개발 환경 (윈도우 + PowerShell + Docker Desktop)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# 백그라운드 실행
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 컨테이너 중지
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# 테스트 실행
docker-compose exec backend pytest tests/ -v
```

### 접속 정보
- 프론트엔드: http://localhost:5174
- 백엔드: http://localhost:8001
- API 문서: http://localhost:8001/docs

## 현재 개발 상황

### 완료된 주요 기능
- **진짜 현금 자산 처리**: asset_type 필드로 현금('cash')과 주식('stock') 구분
- **Pydantic V2 완전 마이그레이션**: 모든 deprecated 경고 제거
- **Tailwind CSS 마이그레이션**: React Bootstrap에서 Tailwind CSS로 완전 전환
- **React Icons 도입**: 이모지 대신 react-icons 라이브러리로 전문적 UI 구현
- **테이블 레이아웃 최적화**: 포트폴리오 테이블의 열 너비 고정으로 UI 겹침 문제 해결
- **종목 선택 UI 개선**: 드롭다운과 직접 입력을 분리한 직관적인 인터페이스
- **백테스트 결과 오류 수정**: 포트폴리오 구성에서 올바른 심볼 표시 (AAPL_0 → AAPL)
- **Jenkins 배포 디버깅**: 환경변수 확인 및 브랜치 조건 개선으로 배포 문제 해결
- **네이버 뉴스 API**: 70+ 종목 지원, 날짜별 필터링, 자동 콘텐츠 정제
- **완전 오프라인 모킹 시스템**: CI/CD 안정성 극대화

### Jenkins CI/CD 파이프라인 상태
- **Frontend Tests**: 23/23 통과 (100%)
- **Backend Tests**: 65/68 통과 (95.3% + 3개 정상 스킵)
- **빌드 및 배포**: 모든 단계 성공
- **크로스 플랫폼 호환성**: Windows CRLF → Unix LF 완전 해결

## 개발 규칙

### 코드 변경 체크리스트
- 새 전략 추가: `backend/app/services/strategy_service.py`에 Strategy 클래스와 `_strategies` 엔트리 추가
- 외부 라이브러리: `backend/requirements.txt`에 추가
- 새 API: `backend/app/api/v1/endpoints/`에 추가, Response/Request 모델은 `backend/app/models/`에 확장
- 현금 자산: asset_type='cash'인 경우 symbol은 임의값 가능, 데이터 수집 없이 일정한 가치 유지
- 네이버 뉴스: 새 종목 추가 시 `ticker_mapping` 딕셔너리 업데이트
- 시스템 정보: 환경 변수나 버전 정보는 `system.py`와 `ServerStatus.tsx`에 반영

### 프론트엔드 개발 우선순위
1. **UnifiedBacktestForm 리팩터링**: 복잡한 상태를 useReducer와 커스텀 훅으로 분리
2. **공통 컴포넌트 라이브러리**: 재사용 가능한 UI 컴포넌트 구축
3. **God Component 분리**: 500줄 이상 컴포넌트들을 단일 책임 원칙에 따라 분리
4. **성능 최적화**: React.memo, useMemo, useCallback을 통한 렌더링 최적화
5. **상수 및 타입 정리**: 매직 넘버/문자열 제거 및 TypeScript 타입 안정성 확보

### 커밋 메시지 규칙
- **형식**: `type: 간결한 제목` (이모지 사용 금지)
- **본문**: 필요시 상세 설명 추가 (불필요한 수식어 제거)
- **예시**: `fix: TypeScript 빌드 오류 해결`, `feat: 현금 자산 처리 기능 추가`

### UI/UX 규칙
- **이모지 금지**: 모든 UI 텍스트, 문서, 커밋 메시지에서 이모지 사용 금지
- **React Icons 사용**: 시각적 요소가 필요한 경우 react-icons 라이브러리 사용
- **일관성**: 텍스트 기반의 깔끔하고 전문적인 인터페이스 유지
- **접근성**: 스크린 리더 호환성을 위한 의미있는 텍스트 사용

### 문서화 규칙
- 코드 수정 시 관련 마크다운 문서 최신화 필수
- 백엔드 문서: `backend/doc/`, 프론트엔드 문서: `frontend/doc/`
- 디렉터리 계층 구조에 맞는 문서 배치

## 주요 위치

### 중요 파일
- 전략 등록: `backend/app/services/strategy_service.py`
- 데이터 수집: `backend/app/utils/data_fetcher.py` (yfinance 사용)
- 뉴스 API: `backend/app/api/v1/endpoints/naver_news.py`
- 설정 관리: `backend/app/core/config.py`

### 문서 위치
- 백엔드 개발 가이드: `backend/doc/README.md`
- 테스트 아키텍처: `backend/doc/TEST_ARCHITECTURE.md`
- 현금 자산 처리: `backend/doc/CASH_ASSETS.md`
- 프론트엔드 개발 가이드: `frontend/doc/README.md`
- Jenkins 배포 문제해결: `JENKINS_DEPLOY_TROUBLESHOOTING.md`

## 외부 의존성

### API 키 필요
- **네이버 검색 API**: NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
- **yfinance**: API 키 불필요

### 데이터베이스
- **MySQL**: 캐시 저장소 (윈도우: host.docker.internal, 운영: 127.0.0.1)

## 제한 사항

### 환경별 고려사항
- **윈도우 도커**: `host.docker.internal` 사용 필수
- **우분투 CI/CD**: MySQL 직접 접근 불가, 완전 오프라인 모킹 사용
- **포트 매핑**: 프론트엔드 5174:5174, 백엔드 8001:8000

### 기술적 제약
- **yfinance**: 시장 휴일/주말 데이터 없음, 일일 API 제한 존재
- **TypeScript strict 모드**: 사용하지 않는 변수 선언 시 빌드 실패
- **Pydantic V2**: @field_validator, json_schema_extra, lifespan 패턴 등 최신 문법 사용

## To-Do 우선순위

### 1. High (비즈니스 핵심 기능)
- [x] 진짜 현금 자산 처리: asset_type 필드로 현금과 주식 구분, 무위험 자산으로 0% 수익률 보장
- [ ] 백테스트 결과 개선: 월별/연도별 수익률 분석, 베타 계수, 최대 연속 손실 기간 등 추가 통계 제공
- [ ] 회원 가입 기능: 사용자 관리 시스템 구축
- [ ] 내 포트폴리오 저장 기능: 사용자별 포트폴리오 관리

### 2. Medium (사용자 경험 개선)
- [x] 폼 상태 관리 개선: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer로 리팩토링 완료
- [x] TypeScript 타입 안정성: 이벤트 핸들러 타입 명시로 any 타입 제거 완료
- [ ] 테스트 커버리지 향상: 단위/통합/E2E 테스트 강화

### 3. Low (고급 기능 및 확장)
- [ ] OpenAI API 포트폴리오 적합성 분석: AI 기반 투자 성향 분석
- [ ] 커뮤니티 기능: 수익률 공유 및 랭킹 시스템
- [ ] 주식 티커 자동 완성: 자연어 → 티커 자동 변환

### 4. React 프론트엔드 리팩터링 계획

#### 4.1. 컴포넌트 분리 (Component Separation) ✅ 완료
**목표**: God Component 해결 및 단일 책임 원칙 적용

- [x] **UnifiedBacktestForm.tsx (515줄 → 166줄) 분리 완료**
  - [x] PortfolioForm: 포트폴리오 입력 테이블 분리 (145줄)
  - [x] StrategyForm: 전략 선택 및 파라미터 설정 분리 (65줄)  
  - [x] DateRangeForm: 날짜 범위 선택 분리 (30줄)
  - [x] CommissionForm: 수수료 및 리밸런싱 설정 분리 (45줄)

- [x] **UnifiedBacktestResults.tsx (546줄 → 48줄) 분리 완료**
  - [x] ResultsHeader: 백테스트 결과 헤더 및 요약 정보 분리 (41줄)
  - [x] ChartsSection: 차트 영역 분리 (포트폴리오/단일 종목 조건부 렌더링) (381줄)
  - [x] AdditionalFeatures: 추가 기능 (뉴스, 환율 등) 분리 (69줄)

- [x] **StockVolatilityNews.tsx (495줄 → 199줄) 분리 완료**
  - [x] VolatilityChart: 변동성 차트 컴포넌트 분리 → VolatilityTable로 구현 (73줄)
  - [x] NewsModal: 뉴스 모달 컴포넌트 분리 (107줄)
  - [x] VolatilityTable: 변동성 테이블 컴포넌트 분리 (73줄)

#### 4.2. 상태 관리 개선 (State Management) ✅ 완료
**목표**: 복잡한 폼 상태 최적화 및 서버 상태 분리

- [x] **UnifiedBacktestForm 상태 통합**
  - [x] useReducer로 portfolio, dates, strategy, params 통합 관리
  - [x] 폼 검증 로직을 별도 훅으로 분리: `useFormValidation`
  - [x] 전략 파라미터 로직 분리: `useStrategyParams`
  - [x] 포트폴리오 관리 로직 분리: `usePortfolio`

- [x] **커스텀 훅 시스템 구축**
  - [x] `useBacktestForm`: 백테스트 폼 상태 및 검증 로직 통합
  - [x] `usePortfolio`: 포트폴리오 추가/삭제/수정/검증 로직
  - [x] `useFormValidation`: 폼 검증 및 에러 관리
  - [x] `useStrategyParams`: 전략 파라미터 관리 및 검증

- [x] **Context API 활용**
  - [x] BacktestContext: 백테스트 관련 전역 상태 관리
  - [x] 중복된 props drilling 제거 준비 완료

#### 4.3. 커스텀 훅 추출 (Custom Hooks)
**목표**: 로직과 뷰 분리, 재사용성 향상

- [ ] **폼 관련 훅**
  - [ ] `useBacktestForm`: 백테스트 폼 상태 및 검증 로직
  - [ ] `usePortfolio`: 포트폴리오 추가/삭제/수정 로직
  - [ ] `useFormInput`: 공통 입력 필드 로직

- [ ] **데이터 페칭 훅**
  - [ ] `useStockPrice`: 주가 데이터 페칭 및 캐싱
  - [ ] `useVolatilityNews`: 변동성 뉴스 데이터 관리
  - [ ] `useExchangeRate`: 환율 데이터 페칭

- [ ] **UI 상태 훅**
  - [ ] `useModal`: 모달 상태 관리 (뉴스, 차트 등)
  - [ ] `useDropdown`: 드롭다운 상태 관리
  - [ ] `useTooltip`: 툴팁 상태 관리

#### 4.4. 성능 최적화 (Performance)
**목표**: 불필요한 리렌더링 방지 및 메모이제이션

- [ ] **메모이제이션 적용**
  - [ ] React.memo: 차트 컴포넌트들 (EquityChart, OHLCChart 등)
  - [ ] useMemo: 차트 데이터 변환 로직, 필터링된 옵션 리스트
  - [ ] useCallback: 이벤트 핸들러 함수들

- [ ] **코드 분할**
  - [ ] React.lazy: 큰 차트 라이브러리 지연 로딩
  - [ ] 뉴스 모달, 상세 차트 등 조건부 로딩

- [ ] **성능 측정**
  - [ ] React DevTools Profiler로 병목 지점 확인
  - [ ] Bundle Analyzer로 번들 크기 최적화

#### 4.5. 코드 표준화 및 재사용성 (DRY Principle)
**목표**: 중복 코드 제거 및 일관성 확보

- [ ] **공통 컴포넌트 라이브러리**
  - [ ] FormField: 라벨, 입력, 에러 메시지 통합 컴포넌트
  - [ ] LoadingSpinner: 통일된 로딩 표시 컴포넌트
  - [ ] ErrorMessage: 표준화된 에러 표시 컴포넌트
  - [ ] DataTable: 재사용 가능한 테이블 컴포넌트

- [ ] **상수 및 타입 정의 통합**
  - [ ] UI 상수: `UI_CONSTANTS.ts` (색상, 크기, 애니메이션 등)
  - [ ] 스타일 클래스: `STYLE_CLASSES.ts` (자주 사용되는 Tailwind 조합)
  - [ ] API 타입: `api-types.ts` 확장 및 정리

- [ ] **유틸리티 함수 정리**
  - [ ] 날짜 포맷팅: `dateUtils.ts`
  - [ ] 숫자 포맷팅: `numberUtils.ts` 
  - [ ] 차트 데이터 변환: `chartUtils.ts`

#### 4.6. 매직 넘버/문자열 제거
**목표**: 하드코딩된 값들을 의미있는 상수로 변경

- [ ] **UI 상수 정의**
  - [ ] `UI_CONSTANTS.ts`: 자주 사용되는 className 조합
  - [ ] `CHART_CONFIG.ts`: 차트 기본 설정값들
  - [ ] `VALIDATION_RULES.ts`: 폼 검증 규칙 확장

- [ ] **텍스트 상수화**
  - [ ] `MESSAGES.ts`: 에러 메시지, 성공 메시지 등
  - [ ] `LABELS.ts`: UI 라벨 텍스트들

#### 4.7. 테스트 코드 강화
**목표**: 리팩터링 안정성 확보

- [ ] **단위 테스트 추가**
  - [ ] 커스텀 훅 테스트
  - [ ] 유틸리티 함수 테스트
  - [ ] 컴포넌트 단위 테스트

- [ ] **통합 테스트**
  - [ ] 백테스트 플로우 전체 테스트
  - [ ] API 모킹 테스트

#### 리팩터링 우선순위 (업데이트: 2024-12-19)
1. **✅ UnifiedBacktestForm 컴포넌트 분리 완료** (가장 복잡한 상태 관리)
   - PortfolioForm, StrategyForm, DateRangeForm, CommissionForm으로 분리
   - 515줄에서 166줄로 축소 (68% 감소), 각 컴포넌트는 단일 책임 원칙 준수
   - TypeScript 타입 안정성 확보 및 props 인터페이스 정의
2. **✅ 상태 관리 개선 완료** (복잡한 상태 로직 분리)
   - useReducer 기반 통합 상태 관리 시스템 구축
   - 5개 전문화된 커스텀 훅 (useBacktestForm, usePortfolio, useFormValidation, useStrategyParams, BacktestContext)
   - 타입 안전성과 재사용성을 고려한 아키텍처 설계
3. **✅ 4.1 컴포넌트 분리 완료** (God Component 해결)
   - UnifiedBacktestResults: 546줄 → 48줄 (91% 감소)
   - StockVolatilityNews: 495줄 → 199줄 (60% 감소)
   - 총 7개의 새로운 전문화된 컴포넌트 생성
4. **공통 컴포넌트 라이브러리 구축** (재사용성 확보)
5. **성능 최적화** (사용자 경험 개선)
6. **테스트 코드 보강** (안정성 확보)

## 참고 명령어

### 개발 효율성
- **실시간 개발**: Docker 볼륨 마운트(`./backend:/app`)로 로컬 파일 수정 시 컨테이너에 즉시 반영
- **테스트**: `docker-compose exec backend pytest tests/ -v` (docker cp 불필요)
- **재빌드**: 새 패키지 의존성 추가 시에만 `--build` 플래그 필요

### CI/CD
- **젠킨스**: main 브랜치 푸시 시 자동 실행
- **테스트 분리**: 프론트엔드 `npm test`, 백엔드 `pytest` 각각 별도 스테이지
- **배포**: scp 파일 복사 + 직접 실행 방식으로 안정성 확보

- 항상 코드를 스캔하기 전에 마크다운 문서들을 정독해.