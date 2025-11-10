# Backtesting Frontend

**라고할때살걸** - 트레이딩 전략 백테스팅 플랫폼 프론트엔드

## 🚀 기술 스택

- **React 18** + **TypeScript**
- **Vite** (빌드 도구)
- **Vitest** (테스트 프레임워크)
- **shadcn/ui** (UI 컴포넌트)
- **Recharts** (차트 라이브러리)
- **React Router** (라우팅)
- **MSW** (API 모킹)

## 📦 설치 및 실행

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

## 📁 디렉토리 구조 규칙

### 컴포넌트 배치

#### `src/components/`
**역할**: 앱 레벨 전역 컴포넌트
- ErrorBoundary (전역 에러 처리)
- Header (앱 헤더)
- ThemeSelector (테마 선택)

**사용 시기**: 앱 전체에서 단 한 번만 사용되는 레이아웃 컴포넌트

#### `src/shared/components/`
**역할**: 재사용 가능한 공통 비즈니스 컴포넌트
- FormField, FormSection (폼 관련)
- ChartLoading, LoadingSpinner (로딩 상태)
- ErrorMessage (에러 표시)
- FinancialTermTooltip (금융 용어 툴팁)

**사용 시기**: 여러 feature에서 재사용 가능한 비즈니스 로직을 포함한 컴포넌트

#### `src/shared/ui/`
**역할**: shadcn/ui 기반 순수 UI 컴포넌트
- Button, Input, Card, Dialog 등 (17개)

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
- chartUtils.ts (차트 데이터 변환)
- dateUtils.ts (날짜 포맷팅)
- formatters.ts (숫자, 통화 포맷)
- numberUtils.ts (숫자 계산)

**사용 시기**: 여러 feature에서 재사용 가능한 순수 함수

#### `src/features/*/utils/`
**역할**: Feature 전용 유틸리티
- 해당 feature의 비즈니스 로직 헬퍼

**사용 시기**: 특정 도메인에만 종속된 유틸리티

---

### 임포트 규칙

#### ✅ 권장 패턴
```typescript
// 절대 경로 사용 (tsconfig paths)
import { Button } from '@/shared/ui/button';
import { FormField } from '@/shared/components';
import { cn } from '@/lib/utils';
import { formatCurrency } from '@/shared/lib/utils/formatters';
```

#### ❌ 금지 패턴
```typescript
// 3단계 이상 상대 경로 금지
import { Button } from '../../../shared/ui/button';  // ❌

// 순환 의존 금지
// Feature A → Feature B 임포트 금지
```

---

## 🏗️ 아키텍처 원칙

### 1. Feature-First Architecture
각 feature는 독립적인 모듈로 관리:
```
features/backtest/
├── api/          # API 호출 계층
├── components/   # UI 컴포넌트
├── hooks/        # 비즈니스 로직 훅
├── model/        # 상태 관리 + 타입
├── services/     # 비즈니스 로직
└── utils/        # Feature 전용 유틸
```

### 2. 명확한 계층 분리
```
API → Service → Hooks → Components
```

### 3. 높은 응집도, 낮은 결합도
- 관련 코드는 가까이 배치
- Feature 간 의존성 최소화
- Shared 레이어를 통한 공유

---

## 🧪 테스트

### 테스트 작성 위치
```
src/features/backtest/components/BacktestForm.tsx
src/features/backtest/components/__tests__/BacktestForm.test.tsx
```

### 테스트 실행
```bash
npm run test              # Watch 모드
npm run test:run          # 1회 실행
npm run test:coverage     # 커버리지 (17.13%)
npm run test:ui           # UI 모드
```

### 현재 테스트 통계
- **테스트 파일**: 13개
- **테스트 케이스**: 98개
- **통과율**: 100%
- **커버리지**: 17.13% (핵심 로직 70~99%)

---

## 📊 주요 컴포넌트

### Pages (라우트 진입점)
- `HomePage.tsx` - 단일 종목 백테스트
- `PortfolioPage.tsx` - 포트폴리오 백테스트

### Features
- `features/backtest/` - 백테스트 전용 로직 (60+ files)

### Shared
- `shared/components/` - 공통 비즈니스 컴포넌트 (9 files)
- `shared/ui/` - shadcn/ui 컴포넌트 (17 files)
- `shared/hooks/` - 공통 훅 (5 files)
- `shared/lib/utils/` - 범용 유틸리티 (5 files)

---

## 🎨 스타일링

- **Tailwind CSS** - 유틸리티 퍼스트
- **CSS Variables** - 테마 시스템 (4개 테마)
- **shadcn/ui** - 컴포넌트 디자인 시스템

---

## 🔧 개발 도구

### 린트 및 타입 체크
```bash
npm run lint          # ESLint
npm run lint:fix      # 자동 수정
npm run type-check    # TypeScript 타입 체크
```

### 빌드 분석
```bash
npm run build:analyze  # 번들 크기 분석
```

---

## 📚 추가 문서

- [TEST.md](./TEST.md) - 테스트 가이드
- [CODEBASE_STRUCTURE_ANALYSIS.md](./CODEBASE_STRUCTURE_ANALYSIS.md) - 구조 상세 분석
- [TEST_IMPROVEMENT_REPORT.md](./TEST_IMPROVEMENT_REPORT.md) - 테스트 개선 내역
- [TEST_EXECUTION_SUMMARY.md](./TEST_EXECUTION_SUMMARY.md) - 테스트 실행 결과

---

## 🤝 기여 가이드

### 새 컴포넌트 추가 시
1. 적절한 위치 선택 (위 규칙 참조)
2. 테스트 파일 함께 작성
3. `index.ts`에 export 추가 (shared의 경우)

### 새 Feature 추가 시
```bash
mkdir -p src/features/new-feature/{api,components,hooks,model,services,utils}
```

### shadcn/ui 컴포넌트 추가
```bash
npx shadcn@latest add <component-name>
# 자동으로 src/shared/ui/에 생성됨
```

---

## 📄 라이선스

MIT

---

**버전**: 1.6.10  
**최종 업데이트**: 2025-11-10
