# 프론트엔드 클린코드 리팩터링 계획

**작성일**: 2025-11-16
**상태**: 계획 수립 완료
**목표**: 클린 코드 원칙에 따른 구조 개선 및 유지보수성 향상

---

## 현황 분석

### 코드 품질 지표

**컴포넌트 크기**:
- 최대 컴포넌트: 643줄 (PortfolioForm.tsx)
- 400줄 이상: 2개 파일
- 200줄 이상: 5개 파일

**주요 문제점**:
1. 거대한 컴포넌트 (Single Responsibility Principle 위반)
2. 비즈니스 로직이 컴포넌트에 혼재
3. UI 로직과 데이터 처리 로직 미분리
4. 반복되는 패턴 (모바일/데스크톱 레이아웃 중복)
5. 하드코딩된 상수 및 매직 넘버

**강점**:
- Feature-Sliced Design 아키텍처 준수
- Custom hooks로 로직 분리 시도
- TypeScript 타입 안전성 확보
- Zustand + useReducer 상태 관리 패턴

---

## Phase 1: 대형 컴포넌트 분할

### 1.1. PortfolioForm.tsx 분할 (643줄)

**문제**: 모바일/데스크톱 레이아웃, 테이블 렌더링, DCA 계산 로직이 하나의 파일에 집중

**해결**: 관심사 분리를 통한 독립 컴포넌트 추출

분리 대상:
- **DcaPreview.tsx** - DCA 프리뷰 컴포넌트
- **PortfolioMobileCard.tsx** - 모바일 카드 레이아웃
- **PortfolioTable.tsx** - 데스크톱 테이블 레이아웃
- **PortfolioInputModeToggle.tsx** - 입력 모드 전환 버튼
- **PortfolioSummary.tsx** - 총 투자금 및 비중 요약

**예상 결과**:
- 메인 컴포넌트 643줄 → 150줄 이하
- 각 하위 컴포넌트 50~150줄
- 컴포넌트 재사용성 향상

### 1.2. BacktestResults.tsx 분할 (460줄)

**문제**: 리포트 생성 로직(generateReportText)이 컴포넌트 내부에 존재

**해결**: 비즈니스 로직을 서비스 레이어로 이동

분리 대상:
- **services/reportGenerator.ts** - 리포트 생성 로직 (순수 함수)
- **PortfolioReportSection.tsx** - 포트폴리오 리포트 섹션
- **SingleStockReportSection.tsx** - 단일 종목 리포트 섹션
- **ExportButtons.tsx** - 내보내기 버튼 그룹

**예상 결과**:
- 컴포넌트 460줄 → 150줄 이하
- 비즈니스 로직 테스트 가능
- 리포트 형식 변경 용이

### 1.3. HomePage.tsx 간소화 (258줄)

**문제**: 랜딩 페이지의 모든 섹션이 하나의 파일에 존재

**해결**: 섹션별 컴포넌트 분리

분리 대상:
- **landing/HeroSection.tsx** - 히어로 섹션
- **landing/WhatIsBacktestSection.tsx** - 백테스트 설명 섹션
- **landing/FeaturesSection.tsx** - 기능 소개 섹션
- **landing/GetStartedSection.tsx** - 시작하기 섹션

**예상 결과**:
- 메인 페이지 258줄 → 50줄 이하 (섹션 조합만)
- 각 섹션 독립적 수정 가능
- 재사용 가능한 랜딩 컴포넌트

---

## Phase 2: 비즈니스 로직 분리

### 2.1. 계산 로직 서비스화

**문제**: 컴포넌트 내부에 산재된 계산 로직

**해결**: services 디렉토리로 순수 함수 이동

생성할 서비스:
- **services/portfolioCalculator.ts**
  - calculateWeightPercent()
  - calculateDcaAdjustedTotal()
  - calculateStockTotalAmount()

- **services/backtestMetrics.ts**
  - formatMetricValue()
  - calculateReturns()
  - calculateDrawdown()

- **services/reportGenerator.ts**
  - generateTextReport()
  - generateCSVReport()
  - generateJSONReport()

**예상 결과**:
- 순수 함수로 테스트 용이
- 로직 재사용성 증가
- 컴포넌트는 UI 렌더링에만 집중

### 2.2. 데이터 변환 로직 분리

**문제**: API 응답을 컴포넌트에서 직접 변환

**해결**: utils 디렉토리에 변환 함수 생성

생성할 유틸리티:
- **utils/backtestTransformers.ts**
  - transformBacktestResult()
  - transformPortfolioData()
  - transformChartData()

- **utils/chartDataProcessors.ts**
  - processEquityData()
  - processTradeSignals()
  - sampleChartData() (이미 존재, 확장)

**예상 결과**:
- 데이터 변환 로직 중앙화
- 타입 안전성 강화
- 테스트 커버리지 향상

---

## Phase 3: 중복 코드 제거

### 3.1. 공통 UI 패턴 추출

**문제**: 반복되는 UI 패턴이 여러 컴포넌트에 중복

**해결**: 재사용 가능한 컴포넌트 생성

생성할 공통 컴포넌트:
- **shared/components/forms/FormFieldGroup.tsx**
  - Label + Input + 에러 메시지 조합

- **shared/components/tables/ResponsiveTable.tsx**
  - 모바일 카드 / 데스크톱 테이블 자동 전환

- **shared/components/stats/MetricCard.tsx**
  - 통계 지표 카드 (재사용 가능)

- **shared/components/charts/ChartContainer.tsx**
  - 차트 공통 래퍼 (로딩, 에러, 빈 상태 처리)

**예상 결과**:
- 코드 중복 50% 이상 감소
- 일관된 UI/UX
- 컴포넌트 작성 시간 단축

### 3.2. 상수 및 설정 통합

**문제**: 하드코딩된 값이 여러 파일에 산재

**해결**: 중앙 집중식 상수 관리

통합 대상:
- **model/constants/chartConfig.ts**
  - 차트 색상, 스타일, 옵션

- **model/constants/formatters.ts**
  - 숫자, 날짜, 통화 포맷터

- **model/constants/uiConfig.ts**
  - 반응형 브레이크포인트
  - 테이블 페이지 크기

**예상 결과**:
- 설정 변경 용이
- 일관된 스타일링
- 매직 넘버 제거

---

## Phase 4: 타입 안전성 강화

### 4.1. 타입 정의 개선

**문제**: any 타입 사용, 불완전한 타입 정의

**해결**: 엄격한 타입 정의 및 검증

개선 대상:
- **model/types/api.ts**
  - API 응답 타입 정확히 정의
  - Zod 스키마로 런타임 검증 추가

- **model/types/chart.ts**
  - 차트 데이터 타입 명확화
  - Recharts 타입과 정확히 매핑

- **tsconfig.json 강화**
  ```json
  {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true
  }
  ```

**예상 결과**:
- 런타임 에러 사전 방지
- IDE 자동완성 개선
- 리팩터링 안전성 향상

### 4.2. Prop 타입 명확화

**문제**: 선택적 prop과 필수 prop 구분 불명확

**해결**: 명시적 타입 정의 및 기본값 설정

개선 패턴:
```typescript
// Before
interface Props {
  data?: SomeData;
  onSubmit?: () => void;
}

// After
interface Props {
  data: SomeData;  // 필수
  onSubmit?: () => void;  // 선택적, 기본 동작 존재
}

const Component: React.FC<Props> = ({
  data,
  onSubmit = () => {}
}) => {
  // ...
}
```

---

## Phase 5: 성능 최적화

### 5.1. 메모이제이션 전략

**현황**: 일부 컴포넌트만 최적화

**개선**: 체계적 메모이제이션 적용

적용 대상:
- 무거운 계산 함수 → useMemo
- 콜백 함수 → useCallback
- 순수 컴포넌트 → React.memo

적용 기준:
- 리스트 아이템 컴포넌트
- 차트 컴포넌트
- 복잡한 계산 로직

### 5.2. 코드 스플리팅 확대

**현황**: LazyChartComponents만 lazy loading

**개선**: 더 많은 컴포넌트 lazy loading

추가 대상:
- 랜딩 페이지 섹션 (페이지 이동 후 로드)
- 모달 컴포넌트 (열릴 때만 로드)
- 리포트 생성 기능 (사용 시에만 로드)

**예상 결과**:
- 초기 번들 크기 30% 감소
- Time to Interactive 개선

---

## Phase 6: 테스트 커버리지 향상

### 6.1. 단위 테스트 확대

**현황**: 일부 hooks 및 reducer만 테스트

**목표**: 핵심 로직 80% 이상 커버리지

우선순위:
1. 순수 함수 (services, utils) - 100%
2. Custom hooks - 80%
3. Reducer 및 상태 관리 - 100%
4. 컴포넌트 (주요 동작) - 60%

### 6.2. 통합 테스트 추가

**추가 대상**:
- 폼 제출 플로우
- API 호출 및 에러 처리
- 차트 데이터 렌더링
- 사용자 인터랙션 시나리오

**도구**:
- Vitest (단위 테스트)
- React Testing Library (컴포넌트)
- MSW (API 모킹)
- Playwright (E2E, 선택적)

---

## 성과 목표

### 코드 품질

- 최대 컴포넌트 크기: 643줄 → 200줄 이하
- 평균 컴포넌트 크기: 100줄 이하
- 코드 중복: 50% 이상 감소
- TypeScript strict mode 적용

### 성능

- 초기 번들 크기: 30% 감소
- Time to Interactive: 20% 개선
- 차트 렌더링: 기존 최적화 유지

### 테스트

- 단위 테스트 커버리지: 80% 이상
- 통합 테스트: 주요 플로우 100%
- E2E 테스트: 핵심 사용자 시나리오

### 유지보수성

- 컴포넌트 재사용성 증가
- 비즈니스 로직 테스트 가능
- 기능 추가/수정 시간 단축

---

## 실행 계획

### 우선순위

**High (즉시 시작)**:
- Phase 1.1: PortfolioForm 분할
- Phase 2.1: 비즈니스 로직 서비스화
- Phase 4.1: 타입 안전성 강화

**Medium (2주 내)**:
- Phase 1.2: BacktestResults 분할
- Phase 3.1: 공통 UI 패턴 추출
- Phase 6.1: 단위 테스트 확대

**Low (점진적)**:
- Phase 1.3: HomePage 간소화
- Phase 5: 성능 최적화
- Phase 6.2: 통합 테스트 추가

### 예상 기간

- Phase 1: 1주
- Phase 2: 1주
- Phase 3: 3일
- Phase 4: 1주
- Phase 5: 3일
- Phase 6: 1주

**총 예상 기간**: 4-5주

---

## 참고

클린 코드 원칙:
- Single Responsibility Principle (단일 책임 원칙)
- DRY (Don't Repeat Yourself)
- Separation of Concerns (관심사 분리)
- KISS (Keep It Simple, Stupid)
- 명확한 명명 규칙
- 순수 함수 우선
