## To-Do 우선순위

### 1. High (비즈니스 핵심 기능)
- [x] 진짜 현금 자산 처리: asset_type 필드로 현금과 주식 구분, 무위험 자산으로 0% 수익률 보장
- [ ] 백테스트 결과 개선: 월별/연도별 수익률 분석, 베타 계수, 최대 연속 손실 기간 등 추가 통계 제공
- [ ] 회원 가입 기능: 사용자 관리 시스템 구축
- [ ] 내 포트폴리오 저장 기능: 사용자별 포트폴리오 관리

### 2. Medium (사용자 경험 개선)
- [x] 폼 상태 관리 개선: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer로 리팩토링 완료
- [x] TypeScript 타입 안정성: 이벤트 핸들러 타입 명시로 any 타입 제거 완료
- [x] 테스트 커버리지 향상: 단위/통합/E2E 테스트 강화

### 3. Low (고급 기능 및 확장)
- [ ] OpenAI API 포트폴리오 적합성 분석: AI 기반 투자 성향 분석
- [ ] 커뮤니티 기능: 수익률 공유 및 랭킹 시스템
- [ ] 주식 티커 자동 완성: 자연어 → 티커 자동 변환

### 4. React 프론트엔드 리팩터링 계획

#### 4.1. 컴포넌트 분리 (Component Separation)
**목표**: God Component 해결 및 단일 책임 원칙 적용

- [x] **UnifiedBacktestForm.tsx (515줄 → 166줄) 분리 완료**
  - [x] PortfolioForm: 포트폴리오 입력 테이블 분리
  - [x] StrategyForm: 전략 선택 및 파라미터 설정 분리
  - [x] DateRangeForm: 날짜 범위 선택 분리
  - [x] CommissionForm: 수수료 및 리밸런싱 설정 분리

- [x] **UnifiedBacktestResults.tsx (546줄 → 48줄) 분리 완료**
  - [x] ResultsHeader: 백테스트 결과 헤더 및 요약 정보 분리
  - [x] ChartsSection: 차트 영역 분리 (포트폴리오/단일 종목 조건부 렌더링)
  - [x] AdditionalFeatures: 추가 기능 (뉴스, 환율 등) 분리

- [x] **StockVolatilityNews.tsx (495줄 → 133줄) 분리 완료**
  - [x] VolatilityChart: 변동성 차트 컴포넌트 분리 → VolatilityTable로 구현
  - [x] NewsModal: 뉴스 모달 컴포넌트 분리
  - [x] VolatilityTable: 변동성 테이블 컴포넌트 분리

#### 4.2. 상태 관리 개선 (State Management)
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

- [x] **새 분리 컴포넌트 상태 관리 (4.2 확장)**
  - [x] `useStockData`: 주가 데이터 페칭 및 캐싱 (ChartsSection용)
  - [x] `useVolatilityNews`: 변동성 뉴스 데이터 관리 (StockVolatilityNews용)
  - [x] `useModal`: 모달 상태 관리 (범용)
  - [x] 유틸리티 함수 분리: `numberUtils.ts`, `dateUtils.ts`

#### 4.3. 커스텀 훅 추출 (Custom Hooks)
**목표**: 로직과 뷰 분리, 재사용성 향상

- [x] **폼 관련 훅**
  - [x] `useBacktestForm`: 백테스트 폼 상태 및 검증 로직
  - [x] `usePortfolio`: 포트폴리오 추가/삭제/수정 로직
  - [x] `useFormInput`: 공통 입력 필드 로직

- [x] **데이터 페칭 훅**
  - [x] `useStockData`: 주가 데이터 페칭 및 캐싱
  - [x] `useVolatilityNews`: 변동성 뉴스 데이터 관리
  - [x] `useExchangeRate`: 환율 데이터 페칭

- [x] **UI 상태 훅**
  - [x] `useModal`: 모달 상태 관리 (뉴스, 차트 등)
  - [x] `useDropdown`: 드롭다운 상태 관리
  - [x] `useTooltip`: 툴팁 상태 관리

- [x] **추가 완성된 훅들**
  - [x] `useBacktest`: 백테스트 API 호출
  - [x] `useFormValidation`: 폼 검증 로직
  - [x] `useStrategyParams`: 전략 파라미터 관리

- **[완료] 4.4 성능 최적화 완료** (React 성능 패턴 적용)
  - [x] React.memo, useMemo, useCallback 전 차트 컴포넌트 적용
  - [x] Code Splitting: React.lazy + Suspense 인프라 구축
  - [x] Bundle Optimization: Vite manualChunks 설정 및 크기 제한
  - [x] Performance Monitoring: 개발환경 성능 추적 시스템
  - [x] Jenkins 빌드 오류 해결: TypeScript 타입 안정성 확보

#### 4.5. 코드 표준화 및 재사용성 (DRY Principle)
**목표**: 중복 코드 제거 및 일관성 확보

- [x] **공통 컴포넌트 라이브러리**
  - [x] FormField: 라벨, 입력, 에러 메시지 통합 컴포넌트
  - [x] LoadingSpinner: 통일된 로딩 표시 컴포넌트
  - [x] ErrorMessage: 표준화된 에러 표시 컴포넌트
  - [x] DataTable: 재사용 가능한 테이블 컴포넌트

- [x] **상수 및 타입 정의 통합**
  - [x] UI 상수: `UI_CONSTANTS.ts` (색상, 크기, 애니메이션 등)
  - [x] 스타일 클래스: `STYLE_CLASSES.ts` (자주 사용되는 Tailwind 조합)
  - [x] API 타입: `api-types.ts` 확장 및 정리

- [x] **유틸리티 함수 정리**
  - [x] 날짜 포맷팅: `dateUtils.ts`
  - [x] 숫자 포맷팅: `numberUtils.ts` 
  - [x] 차트 데이터 변환: `chartUtils.ts`

- [x] **매직 넘버/문자열 제거**
  - [x] 하드코딩된 값들을 의미있는 상수로 변경
  - [x] 폼 옵션 배열: rebalanceOptions, strategyOptions 등
  - [x] 에러 메시지 표준화: ErrorMessage 컴포넌트로 통합
  - [x] 도움말 텍스트 일관성: helpText prop으로 표준화

- [x] **기존 컴포넌트 적용**
  - [x] CommissionForm: FormField 컴포넌트로 리팩터링 완료
  - [x] 하드코딩된 className을 STYLE_CLASSES 상수로 대체
  - [x] 매직 넘버 제거: min, max, step 값을 의미있는 상수로 정의

#### 4.6. 공통 컴포넌트 라이브러리 확장
**목표**: 추가 재사용 컴포넌트 구축

- [x] **추가 UI 컴포넌트**
  - [x] Badge: 상태 표시용 뱃지 컴포넌트
  - [x] Tooltip: 도움말 툴팁 컴포넌트
  - [x] Modal: 표준화된 모달 다이얼로그
  - [x] Pagination: 페이지네이션 컴포넌트

- [x] **고급 폼 컴포넌트**
  - [x] SearchableSelect: 검색 가능한 드롭다운
  - [x] DateRangePicker: 날짜 범위 선택기
  - [x] ToggleSwitch: 토글 스위치 컴포넌트

- [x] **기존 컴포넌트 적용**
  - [x] StrategyForm: FormField 컴포넌트로 리팩터링 (전략 선택 및 파라미터 입력)
  - [x] DateRangeForm: FormField 컴포넌트로 리팩터링 (날짜 입력)
  - [x] NewsModal: Modal 컴포넌트로 리팩터링 (뉴스 모달 다이얼로그)
  - [x] PortfolioForm: Tooltip과 Badge 컴포넌트 적용 (도움말 및 상태 표시)
  - [x] UI 일관성 확보: 공통 컴포넌트 사용으로 디자인 통일성 향상

#### 4.7. 테스트 코드 강화
**목표**: 리팩터링 안정성 확보

- [x] **단위 테스트 추가**
  - [x] 커스텀 훅 테스트: `useBacktestForm.test.ts` (19개 테스트 케이스)
  - [x] 유틸리티 함수 테스트: `dateUtils.test.ts` (38개 테스트), `numberUtils.test.ts` (57개 테스트)
  - [x] 컴포넌트 단위 테스트: `FormField.test.tsx` (19개 테스트 케이스)

- [x] **테스트 커버리지 완료**
  - [x] 폼 상태 관리: 포트폴리오 CRUD, 날짜 검증, 전략 관리, 설정 관리
  - [x] 날짜 유틸리티: 포맷팅, 검증, 계산, 비즈니스 로직, 한국어 지원
  - [x] 숫자 유틸리티: 통화 포맷, 백분율, 통계 함수, 재무 계산, 검증 로직
  - [x] UI 컴포넌트: 렌더링, 상호작용, 에러 처리, 접근성, 타입별 입력

- [x] **테스트 환경 최적화**
  - [x] Vitest + React Testing Library 통합
  - [x] 브라우저 API 모킹 (matchMedia, IntersectionObserver, ResizeObserver)
  - [x] TypeScript 지원 및 타입 안전성 확보
  - [x] 모든 테스트 통과 (156개 테스트 케이스)

#### 리팩터링 우선순위
1. **[완료] UnifiedBacktestForm 컴포넌트 분리 완료** (가장 복잡한 상태 관리)
   - PortfolioForm, StrategyForm, DateRangeForm, CommissionForm으로 분리
   - 515줄에서 166줄로 축소 (68% 감소), 각 컴포넌트는 단일 책임 원칙 준수
   - TypeScript 타입 안정성 확보 및 props 인터페이스 정의
2. **[완료] 상태 관리 개선 완료** (복잡한 상태 로직 분리)
   - useReducer 기반 통합 상태 관리 시스템 구축
   - 5개 전문화된 커스텀 훅 (useBacktestForm, usePortfolio, useFormValidation, useStrategyParams, BacktestContext)
   - 타입 안전성과 재사용성을 고려한 아키텍처 설계
3. **[완료] 4.1 컴포넌트 분리 완료** (God Component 해결)
   - UnifiedBacktestResults: 546줄 → 48줄 (91% 감소)
   - StockVolatilityNews: 495줄 → 133줄 (73% 감소)
   - 총 7개의 새로운 전문화된 컴포넌트 생성
4. **[완료] 4.2 상태 관리 개선 완료** (새 분리 컴포넌트 최적화)
   - useStockData, useVolatilityNews, useModal 훅 구현 (총 283줄)
   - 유틸리티 함수 분리: numberUtils.ts, dateUtils.ts
   - ChartsSection, StockVolatilityNews 컴포넌트에 훅 적용
5. **[완료] 4.3 커스텀 훅 추출 완료** (로직과 뷰 분리)
   - useExchangeRate, useFormInput, useDropdown, useTooltip 훅 구현 (총 341줄)
   - ExchangeRateChart 컴포넌트 리팩터링으로 훅 적용 검증
   - 재사용 가능한 UI 상태 관리 시스템 구축
6. **[완료] 4.4 성능 최적화 완료** (React 성능 패턴 적용)
   - React.memo, useMemo, useCallback 전 차트 컴포넌트 적용
   - Code Splitting: React.lazy + Suspense 인프라 구축
   - Bundle Optimization: Vite manualChunks 설정 및 크기 제한
   - Performance Monitoring: 개발환경 성능 추적 시스템
   - Jenkins 빌드 오류 해결: TypeScript 타입 안정성 확보
7. **[완료] 4.5 코드 표준화 및 재사용성 완료** (DRY 원칙 적용)
   - 공통 컴포넌트 라이브러리: FormField, LoadingSpinner, ErrorMessage, DataTable (총 430줄)
   - 상수 및 타입 정의 통합: UI_CONSTANTS, STYLE_CLASSES, 확장된 API 타입 (총 380줄)
   - 유틸리티 함수 정리: dateUtils, numberUtils, chartUtils 확장 (총 680줄)
   - 매직 넘버/문자열 제거: 중앙화된 상수 관리 시스템
   - 기존 컴포넌트 적용: CommissionForm에 FormField 적용으로 검증 완료
8. **[완료] 4.6 공통 컴포넌트 라이브러리 확장 완료** (추가 컴포넌트 구축)
   - 추가 UI 컴포넌트: Badge, Tooltip, Modal, Pagination (총 575줄)
   - 고급 폼 컴포넌트: SearchableSelect, DateRangePicker, ToggleSwitch (총 531줄)
   - 통합 export 시스템: common/index.ts 업데이트로 일관된 import 패턴
9. **[완료] 4.7 테스트 코드 강화 완료** (안정성 확보)
   - 커스텀 훅 테스트: useBacktestForm.test.ts (19개 테스트 케이스)
   - 유틸리티 함수 테스트: dateUtils.test.ts (38개), numberUtils.test.ts (57개)
   - 컴포넌트 테스트: FormField.test.tsx (19개 테스트 케이스)
   - 모든 테스트 통과 (156개 테스트 케이스), 완전한 테스트 환경 구축

### 5. 백엔드 리팩터링 (Backend Refactoring)
**목표**: God Class 해결 및 서비스 분리를 통한 유지보수성 향상

#### Phase 1: 서비스 분리 (완료)
- [x] **Strategy 클래스 분리** (우선순위: 최고)
  - [x] SMAStrategy → strategies/implementations/sma_strategy.py 이동 완료
  - [x] RSIStrategy → strategies/implementations/rsi_strategy.py 이동 완료
  - [x] BollingerBandsStrategy → strategies/implementations/bollinger_strategy.py 이동 완료
  - [x] MACDStrategy → strategies/implementations/macd_strategy.py 이동 완료
  - [x] BuyAndHoldStrategy → strategies/implementations/buy_hold_strategy.py 이동 완료
  - [x] StrategyService 간소화: 관리 로직만 유지 (341줄 → 80줄, 77% 감소)

- [x] **BacktestService 분리** (우선순위: 최고, 885줄 → 139줄, 84% 감소)
  - [x] BacktestEngine: 백테스트 실행 핵심 로직 (240줄)
  - [x] OptimizationService: 파라미터 최적화 로직 (301줄)  
  - [x] ChartDataService: 차트 데이터 생성 로직 (198줄)
  - [x] ValidationService: 데이터 검증 및 변환 로직 (121줄)
  - [x] 위임 패턴(Delegation Pattern) 적용으로 기존 API 호환성 유지

- [x] **Pydantic 모델 호환성 수정**
  - [x] BacktestResult 필드명 매핑: 기존 모델과 새 서비스 데이터 호환
  - [x] 날짜 타입 변환: datetime.date → str 자동 변환
  - [x] 테스트 범위 수정: max_drawdown_pct 음수 값 허용 (-80% ~ 0%)

#### Phase 1 결과 요약
- **파일 구조**: 8개 → 13개 (전문화된 서비스)
- **코드 감소**: BacktestService 885줄 → 139줄 (84% 감소), StrategyService 341줄 → 80줄 (77% 감소)
- **아키텍처**: God Class → 단일 책임 원칙(SRP) 적용
- **테스트**: 11개 테스트 통과, 1개 스킵 (포트폴리오 테스트)
- **호환성**: 기존 API 인터페이스 완전 유지, 위임 패턴으로 안정성 확보

#### Phase 2: 아키텍처 패턴 도입 (완료)
- [x] **Repository Pattern 도입**
  - [x] BacktestRepository: 백테스트 결과 저장/조회 (인메모리 및 향후 MySQL 지원)
  - [x] DataRepository: yfinance 캐시 데이터 관리 분리 (메모리/MySQL 계층 지원)
  - [x] 인터페이스 기반 의존성 주입 시스템 구축

- [x] **Factory Pattern 적용**
  - [x] StrategyFactory: 전략 인스턴스 생성 및 파라미터 검증 관리
  - [x] ServiceFactory: 서비스 인스턴스 생성 및 의존성 주입

#### Phase 2 결과 요약
- **파일 구조**: 13개 → 19개 (Repository 6개, Factory 2개 추가)
- **아키텍처 패턴**: Repository Pattern + Factory Pattern + 의존성 주입 시스템
- **코드 품질**: 인터페이스 기반 설계로 테스트 가능성 및 확장성 확보
- **호환성**: 기존 API 100% 호환 유지, 11개 테스트 통과 (1개 스킵)
- **의존성 관리**: 서비스 간 느슨한 결합, 인터페이스 기반 의존성 주입

#### Phase 3: Domain-Driven Design (DDD) 아키텍처 (완료)
- [x] **도메인 기반 재구성 (Domain Separation)**
  - [x] **Backtest Domain**: 백테스트 실행, 전략 관리, 결과 분석
    - [x] Value Objects: DateRange, PerformanceMetrics (불변 비즈니스 값)
    - [x] Entities: BacktestResultEntity, StrategyEntity (식별자 보유 객체)
    - [x] Services: BacktestDomainService, StrategyDomainService (도메인 로직 조율)
  
  - [x] **Portfolio Domain**: 자산 배분, 포트폴리오 관리, 리밸런싱
    - [x] Value Objects: Weight, Allocation (가중치 및 자산 배분 관리)
    - [x] Entities: AssetEntity, PortfolioEntity (자산 및 포트폴리오 객체)
    - [x] Services: PortfolioDomainService (포트폴리오 최적화 및 분석)
  
  - [x] **Data Domain**: 시장 데이터 수집, 캐싱, 관리
    - [x] Value Objects: Price, Volume, Symbol, TickerInfo (시장 데이터 값)
    - [x] Entities: MarketDataEntity, MarketDataPoint (시장 데이터 객체)
    - [x] Services: DataDomainService (데이터 일관성 검증 및 분석)

- [x] **DDD 전술적 패턴 적용**
  - [x] **Value Objects**: 19개 불변 값 객체로 데이터 무결성 보장
  - [x] **Entities**: 8개 엔티티로 비즈니스 객체 생명주기 관리
  - [x] **Domain Services**: 5개 도메인 서비스로 복잡한 비즈니스 로직 조율
  - [x] **도메인 간 협력**: 최소 의존성 및 명확한 인터페이스

- [x] **고급 비즈니스 기능 구현**
  - [x] 포트폴리오 가중치 최적화 (변동성 기반)
  - [x] 자산 간 상관관계 분석 및 매트릭스 계산
  - [x] 포트폴리오 다변화 점수 계산 (허핀달 지수 활용)
  - [x] 데이터 일관성 검증 및 무결성 보장
  - [x] 리밸런싱 거래량 계산 및 주기 제안
  - [x] 가격 변화율, 변동성, 성과 지표 분석

#### Phase 3 결과 요약
- **아키텍처**: 완전한 Domain-Driven Design 적용
- **도메인 분리**: 3개 도메인 (Backtest, Portfolio, Data) 완전 분리
- **코드 구조**: 32개 파일 (19개 값 객체, 8개 엔티티, 5개 도메인 서비스)
- **비즈니스 로직**: 도메인별 캡슐화 및 전문화
- **데이터 무결성**: 불변 값 객체로 스레드 안전성 확보
- **확장성**: 이벤트 기반 아키텍처, CQRS 패턴 적용 준비 완료
- **호환성**: 기존 Phase 1, 2와 완전 호환 유지

#### Phase 4: 서비스 통합 및 이벤트 기반 확장 (완료)
- [x] **도메인 서비스 통합**
  - [x] EnhancedBacktestService: 기존 BacktestService와 도메인 서비스 연동
  - [x] EnhancedPortfolioService: 포트폴리오 도메인 서비스 연동 및 고급 분석 기능
  - [x] 도메인 분석 기능: 전략 추천, 품질 평가, 포트폴리오 최적화

- [x] **이벤트 기반 아키텍처 도입**
  - [x] EventBus 시스템: 중앙 집중식 이벤트 라우팅 및 비동기 처리
  - [x] Domain Events: 17개 비즈니스 이벤트 (백테스트 5개, 포트폴리오 6개, 데이터 6개)
  - [x] Event Handlers: 로깅, 메트릭 수집, 분석, 알림 시스템 구축
  - [x] Event System Manager: 이벤트 시스템 통합 관리 및 상태 모니터링

- [x] **CQRS 패턴 적용**
  - [x] Command/Query 분리: 명령과 조회 책임 분리 아키텍처
  - [x] 7개 커맨드: 백테스트/포트폴리오 실행, 최적화, 리밸런싱, 생성
  - [x] 10개 쿼리: 결과 조회, 히스토리, 차트 데이터, 분석, 시장 데이터
  - [x] CQRS Bus: 커맨드/쿼리 라우팅 및 핸들러 관리 시스템
  - [x] CQRSServiceManager: 통합 매니저로 API 엔드포인트 연동 준비

#### Phase 4 결과 요약
- **아키텍처**: Enhanced Services + Event-Driven + CQRS 패턴 완전 적용
- **파일 구조**: 32개 → 45개 (Enhanced Services 2개, Events 8개, CQRS 5개)
- **서비스 통합**: 도메인 서비스를 활용한 고급 분석 및 추천 시스템
- **이벤트 처리**: 17개 도메인 이벤트와 포괄적 핸들러 시스템
- **CQRS 시스템**: 명령/조회 분리로 확장성 및 성능 최적화
- **비즈니스 인텔리전스**: 메트릭 수집, 분석, 알림 시스템 구축
- **호환성**: 기존 Phase 1-3와 완전 호환, API 인터페이스 확장성 확보

#### Phase 5: 엔터프라이즈 확장 (다음 단계)
- [ ] **API 엔드포인트 통합**
  - [ ] 기존 API를 CQRSServiceManager 기반으로 재구성
  - [ ] Enhanced 서비스를 통한 고급 분석 API 제공
  - [ ] 이벤트 기반 비동기 처리 API 엔드포인트

- [ ] **성능 및 확장성 개선**
  - [ ] 멀티 백테스트 병렬 실행 시스템
  - [ ] 이벤트 스트리밍 및 실시간 알림 시스템
  - [ ] 캐시 전략 최적화: Enhanced 서비스 기반

커버리지 보강

BacktestEngine 예외/폴백 경로: bt.run 예외 시 폴백 결과 생성 검증

파일: backend/app/services/backtest/backtest_engine.py:30
추가 테스트: backend/tests/unit/test_backtest_engine.py
포인트: bt.run을 monkeypatch로 강제 예외 발생 → _create_fallback_result로 생성된 BacktestResult 필드(특히 duration_days, max_drawdown_pct, total_trades, 타입/기본값)와 타임스탬프 존재 검증. 결과가 최소 일관성을 갖는지 확인.
결과 변환의 내결함성: 누락된 통계키/NaN에 대한 safe_float/safe_int 동작

파일: backend/app/services/backtest/backtest_engine.py:210
추가 테스트: backend/tests/unit/test_backtest_engine.py
포인트: stats Series에서 일부 키 제거/NaN 주입 → cagr_pct가 'Return (Ann.) [%]'와 동치로 설정되는지, 누락/NaN 시 기본값 적용되는지 검증.
Repository 동작 테스트: 저장/조회/삭제/사용자별 최신순 정렬/리밋

파일: backend/app/repositories/backtest_repository.py:88
추가 테스트: backend/tests/unit/test_backtest_repository.py
포인트: InMemoryBacktestRepository.save_result() → id 반환/조회 일치, get_user_results(limit) 최신순/개수 제한, delete_result() True/False, get_stats() 합리적 수치.
엔드포인트 통합 테스트 보강

/api/v1/backtest/run 성공/검증 오류/InvalidSymbol 처리

파일: backend/app/api/v1/endpoints/backtest.py:20
추가 테스트: backend/tests/integration/test_backtest_run_endpoint.py
포인트: 정상 200 응답 구조, 잘못된 티커 422 고정 및 detail 메시지 존재, 잘못된 파라미터 422.
/api/v1/backtest/health 헬스체크

파일: backend/app/api/v1/endpoints/backtest.py:71
추가 테스트: backend/tests/integration/test_health_endpoint.py
포인트: 200/503 중 하나, 정상 시 status/message/data_source 키 존재.
/api/v1/optimize/* 최적화 API

파일: backend/app/api/v1/endpoints/optimize.py:16
추가 테스트: backend/tests/integration/test_optimize_endpoints.py
포인트: POST /run 기본 범위로 200 + best_params/best_score, GET /targets·/methods 200 + 필드 유효성.
에러 코드 일관성 강화(테스트 기대값)

docs의 Phase 2(422 일관화)와 테스트 일치
파일: backend/doc/TEST_ARCHITECTURE.md:108
파일: backend/tests/fixtures/expected_results.py:100
제안: invalid_ticker.expected_status_code를 [422]로 축소, invalid_strategy.expected_status_code도 422 우선. 실제 엔드포인트(get_chart_data)는 422로 매핑되어 있어 테스트를 더 엄격히 해도 통과 가능.
성능 테스트 마킹

느린 테스트 명시적 표기로 선택 실행 가능하게
파일: backend/tests/unit/test_data_fetcher.py:238, backend/tests/unit/test_backtest_service.py:163
조치: 위 테스트에 @pytest.mark.slow 추가. 이미 backend/pytest.ini:13에 slow 마커 정의됨.
경계/회귀 테스트 추가

날짜 역순 처리 명확화

파일: backend/tests/unit/test_data_fetcher.py:76
제안: start > end 시 정책(빈 DF 반환 or 422 유도)을 확정하고 이에 맞춘 단정(현재는 느슨). 정책 확정 시 통합 테스트도 동일 기준으로 강화.
차트 데이터 구조 회귀 체크 강화

파일: backend/tests/integration/test_api_endpoints.py:22
제안: summary_stats의 숫자 필드 타입/범위 단정에 profit_factor/win_rate_pct 기본값 처리까지 포함.