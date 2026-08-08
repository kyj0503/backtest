# Backtesting Frontend

**트레이딩 전략 백테스팅 플랫폼 프론트엔드**

## 기술 스택

- **React 19** + **TypeScript 5**
- **Vite 7** (빌드 도구)
- **Vitest 4** (테스트 프레임워크)
- **Tailwind CSS 4** (스타일링, 설정은 `src/index.css`에 CSS-first로 존재)
- **shadcn/ui** (UI 컴포넌트)
- **Recharts 3** (차트 라이브러리)
- **React Router 7** (라우팅)
- **MSW 2** (API 모킹)

## 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 테스트
npm run test          # Watch 모드
npm run test:run      # 1회 실행
npm run test:coverage # 커버리지
npm run test:ui       # UI 모드
```

## 디렉토리 구조 규칙

### 컴포넌트 배치

#### `src/shared/components/`
**역할**: 재사용 가능한 공통 컴포넌트. 용도별 하위 디렉터리로 나뉜다.

| 디렉터리 | 내용 |
|---|---|
| `layout/` | Header, Footer, ErrorBoundary, ThemeSelector |
| `form/` | FormField, FormSection, FormLegend |
| `loading/` | LoadingSpinner, ChartLoading |
| `feedback/` | ErrorMessage |
| `tooltip/` | FinancialTermTooltip |
| `debug/` | PerformanceMonitor |

**사용 시기**: 여러 feature에서 재사용 가능한 컴포넌트

#### `src/shared/ui/`
**역할**: shadcn/ui 기반 순수 UI 컴포넌트
- Button, Input, Card, Dialog 등 (16개)

**사용 시기**: 디자인 시스템 레벨의 재사용 가능한 순수 UI 컴포넌트

#### `src/features/*/components/`
**역할**: Feature 전용 컴포넌트
- 해당 feature에서만 사용
- 다른 feature에 의존하지 않음

**사용 시기**: 특정 도메인(백테스트, 포트폴리오 등)에만 종속된 컴포넌트

---

### 유틸리티 배치

#### `src/lib/utils.ts`
**역할**: shadcn/ui 표준 유틸리티
- `cn()` 함수 (Tailwind CSS 클래스 병합)

**사용 시기**: shadcn/ui 컴포넌트에서 클래스 조합이 필요할 때

**중요**: shadcn/ui 표준 경로이므로 변경 금지!

#### `src/shared/lib/utils/`
**역할**: 범용 유틸리티 함수
- dateUtils.ts (날짜 포맷팅)
- formatters.ts (숫자, 통화 포맷)
- numberUtils.ts (숫자 계산)

(차트 데이터 변환은 `features/backtest/hooks/charts/useChartData.ts`와 `shared/utils/dataSampling.ts`가 담당합니다. 과거 있었던 `chartUtils.ts`는 삭제되었습니다.)

**사용 시기**: 여러 feature에서 재사용 가능한 순수 함수

#### `src/features/*/utils/`
**역할**: Feature 전용 유틸리티
- 해당 feature의 비즈니스 로직 헬퍼

**사용 시기**: 특정 도메인에만 종속된 유틸리티

---

### 임포트 규칙

#### 권장 패턴
```typescript
// 절대 경로 사용 (tsconfig paths)
import { Button } from '@/shared/ui/button';
import { FormField } from '@/shared/components';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/shared/lib/utils/formatters';
```

#### 금지 패턴
```typescript
// 3단계 이상 상대 경로 금지
import { Button } from '../../../shared/ui/button';

// 순환 의존 금지
// Feature A → Feature B 임포트 금지
```

---

## 아키텍처 원칙

### 1. Feature-First Architecture
각 feature는 독립적인 모듈로 관리 (feature 전용 `api/` 계층은 없음 — API 호출은 `services/`가 `shared/api/client.ts`의 axios 인스턴스를 직접 사용):
```
features/backtest/
├── components/   # UI 컴포넌트
├── constants/    # Feature 전용 상수
├── hooks/        # 비즈니스 로직 훅
├── model/        # useReducer 상태 + 타입
├── services/     # API 호출 및 응답 가공 (backtestService.ts 등)
└── utils/        # Feature 전용 유틸
```

### 2. 명확한 계층 분리
```
shared/api (axios) → Service → Hooks → Components
```

### 3. 높은 응집도, 낮은 결합도
- 관련 코드는 가까이 배치
- Feature 간 의존성 최소화
- Shared 레이어를 통한 공유

---

## 테스트

### 테스트 작성 위치
```
src/features/backtest/components/PortfolioBacktestForm.tsx
src/features/backtest/components/__tests__/BacktestForm.test.tsx
```

### 테스트 실행
```bash
npm run test              # Watch 모드
npm run test:run          # 1회 실행
npm run test:coverage     # 커버리지
npm run test:ui           # UI 모드
```

### 현재 테스트 통계
- **테스트 파일**: 17개
- **테스트 케이스**: 112개
- **통과율**: 100%
- **커버리지**: `npm run test:coverage`로 직접 확인하세요 (테스트 파일/케이스 수가 자주 바뀌어 커버리지 수치를 여기 고정해 두지 않습니다).

### 테스트 격리에 관한 주의

`vitest.config.ts`의 `isolate`를 `false`로 바꾸지 말 것. 모든 테스트 파일이 하나의 happy-dom 환경을 공유하게 되는데, vitest는 직전 실행의 파일별 소요시간을 캐시해 실행 순서를 조정하므로 순서가 매번 달라진다. 그 결과 스위트가 flaky해진다 — 실제로 같은 커밋에서 `113 passed`와 `3 failed`가 번갈아 나온 적이 있다.

---

## 주요 컴포넌트

### Pages (라우트 진입점)
- `pages/HomePage.tsx` - 랜딩
- `pages/PortfolioPage.tsx` - 백테스트 (단일 종목 + 포트폴리오)

### Features
- `features/backtest/` - 백테스트 전용 로직 (77 files)

### Shared
- `shared/components/` - 공통 컴포넌트 (12 files, 테스트 제외)
- `shared/ui/` - shadcn/ui 컴포넌트 (16 files)
- `shared/hooks/` - 공통 훅 (1 file: useTheme)
- `shared/lib/utils/` - 범용 유틸리티 (dateUtils, formatters, numberUtils + index)

---

## 스타일링

- **Tailwind CSS 4** - 유틸리티 퍼스트. v4는 JS 설정 파일을 쓰지 않으므로 `tailwind.config.js`는 없고 설정이 `src/index.css`에 있다.
- **CSS Variables** - 테마 시스템 (`src/themes/`에 4개 테마)
- **shadcn/ui** - 컴포넌트 디자인 시스템

### Tailwind 4에서 주의할 점

- 다크 모드는 `@custom-variant dark (&:is(.dark *))`로 정의된다. `useTheme`이 `<html>`에 `.dark`를 토글한다.
- 테마 색상은 `useTheme`이 런타임에 `root.style.setProperty()`로 주입한다. 색상 리터럴을 `@theme` 블록으로 옮기면 빌드타임에 고정되어 테마 전환이 죽는다.
- v4가 자체 `.container`를 방출하므로, v3 동작을 재현한 `.app-container`를 대신 쓴다.

---

## 개발 도구

### 린트 및 타입 체크
```bash
npm run lint             # ESLint (에러 0 강제, 경고 상한 3)
npm run lint:fix         # 자동 수정
npm run type-check       # 프로덕션 코드 타입 체크 (tsconfig.build.json)
npm run type-check:test  # 테스트 코드 타입 체크 (tsconfig.test.json)
```

`type-check`는 테스트 파일을 제외한다. 테스트 코드는 `type-check:test`가 담당하며, 둘 다 CI 게이트에서 실행된다. 테스트만 따로 체크하는 설정이 없던 시절에 삭제된 함수를 import하는 테스트가 8개월간 방치된 적이 있어 분리해 두었다.

`lint`의 경고 상한 3은 현재 남아 있는 `react-hooks/exhaustive-deps` 3건을 고정한 래칫이다. 경고가 늘어나는 것을 막되, 의존성 배열을 강제로 바꾸면 런타임 동작이 달라질 수 있어 아직 해소하지 않았다. 해소하면서 상한도 함께 내리는 것이 목표다.

### 빌드 분석
```bash
npm run build:analyze
```

**주의**: 현재 이 스크립트는 `build`와 동일한 일을 한다. 번들 분석 플러그인이 설치되어 있지 않고 `--mode analyze`에 대응하는 설정도 없다. 실제 분석이 필요하면 `rollup-plugin-visualizer` 등을 붙여야 한다.

---

## CI

`Jenkinsfile`의 `Quality Gate` 스테이지가 `docker build --target test ./backtest_fe`로 아래를 순서대로 실행한다. 하나라도 실패하면 이미지 빌드와 배포에 도달하지 못한다.

```
npm run lint → npm run type-check → npm run type-check:test → npm run test:run
```

이 게이트는 **배포**를 막는다. main 브랜치 보호를 쓰지 않으므로 병합 자체를 막지는 않는다.

---

## 추가 문서

- [docs/architecture/codebase_structure.md](./docs/architecture/codebase_structure.md) - 구조 상세
- [docs/architecture/state_management.md](./docs/architecture/state_management.md) - 상태 관리
- [docs/testing/](./docs/testing/) - 테스트 전략·작성·실행 가이드
- [docs/optimization/](./docs/optimization/) - 차트 성능, 데이터 샘플링
