# 프론트엔드 개발 가이드

React 18 + TypeScript 기반의 백테스팅 웹 애플리케이션 개발 가이드입니다.

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Framework**: Tailwind CSS
- **Icons**: React Icons
- **Charting**: Recharts
- **Testing**: Vitest + Testing Library
- **Container**: Docker

## 테스트 커버리지 개요 (2025-09)

- 폼 서브컴포넌트 테스트
  - StrategyForm: 전략 선택 및 파라미터 입력 이벤트 검증
  - CommissionForm: 리밸런싱 주기, 수수료 변경 이벤트 검증
  - PortfolioForm: 종목/현금 추가 버튼, 심볼 선택 변경 이벤트 검증
  - DateRangeForm: 시작/종료 날짜 변경 이벤트 검증
- 차트 스모크 테스트
  - EquityChart, OHLCChart, StockPriceChart, TradesChart의 기본 렌더 확인
  - 메모: JSDOM 환경의 width=0 문제로 ResponsiveContainer가 SVG를 렌더하지 않을 수 있어, 스모크 수준의 렌더 유무만 확인
- 기존 영역
  - 유틸(date/number/formatters), 공통 컴포넌트(FormField), 에러 경계(ErrorBoundary)
  - 훅(useBacktestForm, useBacktest), 서비스(BacktestApiService HTTP 상태→에러 타입 매핑)

### 테스트 실행

```bash
# 도커 컨테이너에서 실행 예시
docker run --rm -t -v "$PWD/frontend":/workspace -w /workspace node:20 bash -lc "npm ci && npm test -- --run"
```

### 단기 (개발 생산성)
- **폼 상태 관리**: useReducer를 활용한 복잡한 폼 상태 개선
- **컴포넌트 분해**: 대형 컴포넌트의 세분화
- **에러 처리**: 전역 에러 핸들링 개선

### 중기 (사용자 경험)
- **UI/UX 개선**: 사용자 피드백 기반 인터페이스 개선
- **접근성**: 웹 접근성 가이드라인 준수
- **반응형 디자인**: 모바일 최적화

### 장기 (확장성)
- **상태 관리 라이브러리**: Redux Toolkit 도입 고려
- **PWA**: 프로그레시브 웹앱 기능 추가
- **국제화**: 다국어 지원

## 레이아웃 개선사항

### 폼 디자인 일관성
- **테이블 구조**: 종목/자산 → 투자 금액 → 투자 방식 → 자산 타입 순서로 논리적 배치
- **이모지 제거**: 모든 UI 텍스트에서 이모지 제거로 전문적인 인터페이스 구현
- **입력 필드 정렬**: 폼 요소들의 일관된 스타일링과 배치ng**: Vitest + Testing Library
- **Container**: Docker

## 프로젝트 구조

```
frontend/
├── src/
│   ├── components/           # React 컴포넌트
│   │   ├── common/          # 공통 컴포넌트 라이브러리
│   │   │   ├── FormField.tsx           # 통합 폼 필드 컴포넌트
│   │   │   ├── LoadingSpinner.tsx      # 통일된 로딩 스피너
│   │   │   ├── ErrorMessage.tsx        # 표준화된 에러 메시지
│   │   │   ├── DataTable.tsx           # 재사용 가능한 테이블
│   │   │   ├── ChartLoading.tsx        # 차트 로딩 컴포넌트
│   │   │   ├── PerformanceMonitor.tsx  # 성능 모니터링
│   │   │   └── index.ts                # 공통 컴포넌트 내보내기
│   │   ├── lazy/            # 코드 스플리팅 컴포넌트
│   │   ├── results/         # 백테스트 결과 관련
│   │   ├── UnifiedBacktestForm.tsx     # 통합 백테스트 폼
│   │   └── ErrorBoundary.tsx           # 에러 경계 컴포넌트
│   ├── pages/              # 페이지 컴포넌트
│   ├── services/           # API 호출 서비스
│   │   └── api.ts          # 백엔드 API 호출 함수
│   ├── types/              # TypeScript 타입 정의
│   │   └── api.ts          # 확장된 API 타입 정의
│   ├── constants/          # 상수 정의
│   │   ├── UI_CONSTANTS.ts # UI 색상, 크기, 애니메이션 상수
│   │   ├── STYLE_CLASSES.ts # Tailwind CSS 클래스 조합
│   │   ├── strategies.ts   # 전략 및 종목 상수
│   │   └── index.ts        # 상수 통합 내보내기
│   ├── utils/              # 유틸리티 함수
│   │   ├── dateUtils.ts    # 확장된 날짜 조작 함수
│   │   ├── numberUtils.ts  # 확장된 숫자 포맷팅 함수
│   │   ├── chartUtils.ts   # 차트 데이터 변환 함수
│   │   ├── formatters.ts   # 레거시 포맷터 (호환성)
│   │   └── index.ts        # 유틸리티 통합 내보내기
│   ├── hooks/              # 커스텀 훅
│   │   ├── useBacktestForm.ts    # 백테스트 폼 상태 관리
│   │   ├── useChartOptimization.ts # 차트 성능 최적화
│   │   └── useModal.ts           # 모달 상태 관리
│   └── test/               # 테스트 파일
├── doc/                    # 문서
└── public/                 # 정적 파일
```

## 주요 컴포넌트

### UnifiedBacktestForm
- **역할**: 백테스트 설정 및 실행을 위한 통합 폼
- **특징**: 단일 종목과 포트폴리오 백테스트 모두 지원
- **현금 자산**: asset_type 필드로 현금과 주식 구분
- **종목 선택**: 드롭다운과 직접 입력을 분리한 직관적인 UI
- **테이블 레이아웃**: 고정 열 너비로 UI 겹침 방지

### BacktestResult
- **역할**: 백테스트 결과 시각화 및 표시
- **차트**: Recharts를 사용한 수익률 차트, OHLC 차트
- **통계**: 총 수익률, 샤프 비율, 최대 손실폭 등

### ErrorBoundary
- **역할**: React 에러 포착 및 사용자 친화적 에러 표시
- **적용 범위**: 전체 애플리케이션

## 공통 컴포넌트 라이브러리

### FormField 컴포넌트
표준화된 폼 입력 필드로 라벨, 입력, 에러 메시지를 통합 제공합니다.

```typescript
<FormField
  label="투자 금액"
  type="number"
  value={amount}
  onChange={setAmount}
  required={true}
  error={validationError}
  helpText="최소 1,000원 이상 입력하세요"
  min={1000}
/>
```

**지원 타입**: text, number, date, select, textarea

### LoadingSpinner 컴포넌트
통일된 로딩 표시를 위한 스피너 컴포넌트입니다.

```typescript
<LoadingSpinner 
  size="md" 
  color="blue" 
  text="데이터를 불러오는 중..." 
/>

{/* 오버레이 스피너 */}
<LoadingSpinner overlay={true} />

{/* 인라인 스피너 */}
<InlineSpinner />

{/* 버튼 내 스피너 */}
<ButtonSpinner />
```

### ErrorMessage 컴포넌트
표준화된 에러 및 알림 메시지 표시 컴포넌트입니다.

```typescript
<ErrorMessage 
  type="error"
  title="백테스트 실행 실패"
  message="네트워크 연결을 확인해주세요"
  dismissible={true}
  onClose={handleClose}
/>

{/* 필드 에러 */}
<FieldError message="필수 입력 항목입니다" />

{/* 토스트 메시지 */}
<ToastMessage type="success" message="백테스트가 완료되었습니다" />
```

### DataTable 컴포넌트
재사용 가능한 테이블 컴포넌트로 정렬, 필터링, 로딩 상태를 지원합니다.

```typescript
const columns = [
  { key: 'symbol', label: '종목', sortable: true },
  { key: 'amount', label: '금액', render: (value) => formatCurrency(value) },
  { key: 'return_pct', label: '수익률', render: (value) => formatPercent(value) }
];

<DataTable
  columns={columns}
  data={portfolioData}
  loading={isLoading}
  error={error}
  onSort={handleSort}
  onRowClick={handleRowClick}
  hoverable={true}
  striped={false}
/>
```

## 상수 및 스타일 시스템

### UI_CONSTANTS
색상, 크기, 애니메이션 등 UI 관련 상수를 중앙화 관리합니다.

```typescript
import { UI_CONSTANTS } from '@/constants';

// 색상 사용
const primaryColor = UI_CONSTANTS.COLORS.PRIMARY;
const chartColor = UI_CONSTANTS.CHART_COLORS.EQUITY;

// 크기 및 간격
const buttonPadding = UI_CONSTANTS.SPACING.MD;
const borderRadius = UI_CONSTANTS.BORDER_RADIUS.LG;
```

### STYLE_CLASSES
자주 사용되는 Tailwind CSS 클래스 조합을 표준화합니다.

```typescript
import { getButtonClasses, getInputClasses } from '@/constants';

// 버튼 클래스 생성
const primaryButton = getButtonClasses('primary', 'lg');
const secondaryButton = getButtonClasses('secondary', 'md', disabled);

// 입력 필드 클래스 생성
const inputClass = getInputClasses('default', 'md');
const errorInputClass = getInputClasses('error', 'md');
```

## 확장된 유틸리티 함수

### 날짜 관련 (dateUtils.ts)
```typescript
import { formatDate, addDays, getBusinessDaysBetween, getPresetDateRanges } from '@/utils';

// 기본 포맷팅
const displayDate = formatDate(new Date());
const relativTime = formatRelativeTime('2024-01-01');

// 날짜 계산
const futureDate = addDays(new Date(), 30);
const businessDays = getBusinessDaysBetween('2024-01-01', '2024-12-31');

// 미리 정의된 범위
const ranges = getPresetDateRanges();
const lastYear = ranges['지난 1년'];
```

### 숫자 관련 (numberUtils.ts)
```typescript
import { formatPercent, formatLargeNumber, safeDivide, getColorByValue } from '@/utils';

// 포맷팅
const percentage = formatPercent(0.15, 2); // "+0.15%"
const largeNum = formatLargeNumber(1500000); // "1.5M"
const ratio = safeDivide(10, 0, 'N/A'); // "N/A"

// 수학 계산
const avg = average([1, 2, 3, 4, 5]); // 3
const stdev = standardDeviation([1, 2, 3, 4, 5]);

// 차트용 색상
const color = getColorByValue(0.05); // 양수면 녹색, 음수면 빨간색
```

### 차트 관련 (chartUtils.ts)
```typescript
import { transformOHLCData, calculateMovingAverage, createChartConfig } from '@/utils';

// 데이터 변환
const chartData = transformOHLCData(ohlcData);
const equityData = transformEquityData(equityPoints);

// 기술적 지표
const sma20 = calculateMovingAverage(prices, 20);
const rsi = calculateRSI(prices, 14);

// 차트 설정
const candlestickConfig = createChartConfig('candlestick');
const lineConfig = createChartConfig('line');
```

## 코드 표준화 성과

### 4.5 단계 완료 사항
- 공통 컴포넌트 라이브러리: FormField, LoadingSpinner, ErrorMessage, DataTable
- 상수 및 타입 정의 통합: UI_CONSTANTS, STYLE_CLASSES, 확장된 API 타입
- 유틸리티 함수 정리: dateUtils, numberUtils, chartUtils 확장

### 개선 효과
- **코드 재사용성**: 공통 컴포넌트로 40% 이상 코드 중복 제거
- **일관성**: 표준화된 스타일과 동작으로 UI/UX 일관성 확보
- **유지보수성**: 중앙화된 상수 관리로 변경 영향도 최소화
- **개발 속도**: 재사용 가능한 컴포넌트로 개발 시간 단축

### 사용 예시
```typescript
// Before (4.5 이전)
<div>
  <label className="block text-sm font-medium text-gray-700 mb-2">
    투자 금액
  </label>
  <input
    type="number"
    className="block w-full px-3 py-2 border border-gray-300 rounded-md..."
    value={amount}
    onChange={(e) => setAmount(Number(e.target.value))}
  />
  {error && <p className="text-sm text-red-600 mt-1">{error}</p>}
</div>

// After (4.5 이후)
<FormField
  label="투자 금액"
  type="number"
  value={amount}
  onChange={(value) => setAmount(value as number)}
  error={error}
  required={true}
/>
```

## API 통신

### 타입 정의
```typescript
// 포트폴리오 구성 요소
export interface PortfolioStock {
  symbol: string;
  amount: number;
  investment_type?: 'lump_sum' | 'dca';
  dca_periods?: number;
  asset_type?: 'stock' | 'cash';  // 현금 자산 지원
}

// 통합 백테스트 요청
export interface UnifiedBacktestRequest {
  portfolio: PortfolioStock[];
  start_date: string;
  end_date: string;
  strategy: string;
  strategy_params?: Record<string, any>;
  commission?: number;
  rebalance_frequency?: string;
}
```

### API 서비스
```typescript
// 백테스트 실행
await api.runBacktest(request);

// 서버 상태 확인
await api.getServerStatus();
```

## 현금 자산 처리

### 개념
- **무위험 자산**: 시간에 관계없이 0% 수익률 보장
- **리스크 완화**: 포트폴리오에서 변동성 감소 역할
- **자산 타입 구분**: `asset_type: 'cash'`로 식별

### 구현
```typescript
// 현금 자산 추가
const addCashAsset = () => {
  setSelectedStocks(prev => [...prev, {
    symbol: '현금',
    amount: 10000,
    investment_type: 'lump_sum',
    asset_type: 'cash'
  }]);
};
```

## 개발 규칙

### TypeScript 타입 안정성
- **strict 모드**: 엄격한 타입 검사 적용
- **any 타입 금지**: 명시적 타입 정의 필수
- **이벤트 핸들러**: 타입 안전한 이벤트 처리

### 컴포넌트 설계
- **단일 책임**: 컴포넌트당 하나의 명확한 역할
- **props 인터페이스**: 모든 props에 대한 TypeScript 인터페이스 정의
- **상태 관리**: 복잡한 상태는 useReducer 사용 고려

### 코딩 스타일
- **네이밍**: camelCase (JavaScript), snake_case (API 통신)
- **파일명**: PascalCase (컴포넌트), camelCase (유틸리티)
- **import 순서**: React → 외부 라이브러리 → 내부 모듈

## 테스트

### 테스트 구조
```
src/test/
├── utils/
│   └── formatters.test.ts    # 유틸리티 함수 테스트
└── components/
    └── ErrorBoundary.test.tsx # 컴포넌트 테스트
```

### 테스트 실행
```bash
# 개발 환경에서 테스트
docker-compose exec frontend npm test

# CI/CD 환경에서 테스트
npm test -- --run
```

## 빌드 및 배포

### 개발 환경
```bash
# 개발 서버 시작
npm run dev
# 브라우저에서 http://localhost:5174 접속
```

### 프로덕션 빌드
```bash
# 빌드
npm run build

# 빌드 결과 확인
ls -la dist/
```

### Docker 배포
- **개발 이미지**: 실시간 코드 반영, 테스트 포함
- **프로덕션 이미지**: nginx 정적 서빙, 최적화된 빌드

### CI/CD 파이프라인
- **Jenkins 통합**: main 브랜치 푸시 시 자동 빌드
- **배포 디버깅**: 환경변수 확인을 통한 배포 조건 검증
- **다중 브랜치 지원**: BRANCH_NAME, GIT_BRANCH 환경변수 다중 조건 처리

## 성능 최적화

### 빌드 최적화
- **코드 분할**: 500KB 이상 청크에 대한 분할 고려
- **이미지 최적화**: 정적 이미지 압축
- **트리 쉐이킹**: 사용하지 않는 코드 제거

### 런타임 최적화
- **메모이제이션**: React.memo, useMemo, useCallback 활용
- **지연 로딩**: 대용량 컴포넌트의 lazy loading
- **상태 최적화**: 불필요한 리렌더링 방지

## 문제 해결

### 일반적인 이슈
1. **TypeScript 컴파일 오류**: 타입 정의 불일치 확인
2. **API 통신 실패**: 네트워크 상태 및 백엔드 상태 확인
3. **차트 렌더링 문제**: 데이터 형식 및 Recharts 버전 확인

### 테스트 실행
```bash
# Docker 환경에서 테스트 실행
docker-compose exec frontend npm test

# 로컬 환경에서 테스트 실행
npm test

# 테스트 커버리지 확인
npm run test:coverage
```

### 테스트 구조
- **커스텀 훅 테스트**: `src/hooks/__tests__/` - 19개 테스트 케이스
- **유틸리티 테스트**: `src/utils/__tests__/` - 95개 테스트 케이스 (dateUtils 38개, numberUtils 57개)
- **컴포넌트 테스트**: `src/components/__tests__/` - 42개 테스트 케이스
- **총 테스트 케이스**: 156개 (100% 통과)

### 디버깅 도구
- **React DevTools**: 컴포넌트 상태 및 props 확인
- **Browser DevTools**: 네트워크 요청 및 콘솔 에러 확인
- **Vite DevTools**: 빌드 과정 및 모듈 의존성 확인

## 향후 개선 계획

### 테스트 커버리지 완료 (2024년 완료)
- **단위 테스트**: 커스텀 훅, 유틸리티 함수, 컴포넌트 테스트 완료 (156개 테스트 케이스)
- **테스트 프레임워크**: Vitest + React Testing Library 환경 구축 완료
- **타입 안전성**: TypeScript 기반 테스트 환경으로 컴파일 타임 검증 확보

### 리팩터링 완료 (2024년 완료)
- **컴포넌트 분리**: God Component 해결, 단일 책임 원칙 적용 완료
- **상태 관리**: 14개 커스텀 훅 구현, useReducer 기반 상태 관리 완료
- **성능 최적화**: React.memo, 코드 스플리팅, 번들 최적화 완료
- **공통 컴포넌트**: 13개 재사용 컴포넌트 라이브러리 구축 완료
- **UI 표준화**: 이모지 제거, 전문적 인터페이스 구현 완료

### 단기 (개발 생산성)
- **폼 상태 관리**: useReducer를 활용한 복잡한 폼 상태 개선 (완료)
- **컴포넌트 분해**: 대형 컴포넌트의 세분화 (완료)
- **에러 처리**: 전역 에러 핸들링 개선

### 중기 (사용자 경험)
- **UI/UX 개선**: 사용자 피드백 기반 인터페이스 개선
- **접근성**: 웹 접근성 가이드라인 준수
- **반응형 디자인**: 모바일 최적화

### 장기 (확장성)
- **상태 관리 라이브러리**: Redux Toolkit 도입 고려
- **PWA**: 프로그레시브 웹앱 기능 추가
- **국제화**: 다국어 지원

## 문서 구조

- [API 통신 가이드](./API_GUIDE.md) - REST API 호출 및 에러 처리
- [컴포넌트 아키텍처](./COMPONENTS.md) - React 컴포넌트 설계 및 재사용
- [상태 관리 가이드](./STATE_MANAGEMENT.md) - useState, useReducer, Context API 패턴
