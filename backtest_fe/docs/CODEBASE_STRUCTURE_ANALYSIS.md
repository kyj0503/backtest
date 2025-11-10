# 프론트엔드 코드베이스 구조 분석 보고서 🔍

**분석일**: 2025-11-10  
**총 파일 수**: 123개 (테스트 제외)

---

## 📊 현재 구조 개요

```
src/
├── App.tsx, main.tsx                    (2 files) ✅ 적절
├── components/                          (3 files) ⚠️ 역할 모호
│   ├── ErrorBoundary.tsx
│   ├── Header.tsx
│   └── ThemeSelector.tsx
├── lib/                                 (1 file) ⚠️ Re-export만 존재
│   └── utils.ts → @/shared/lib/core/utils
├── pages/                               (2 files) ✅ 적절
│   ├── HomePage.tsx
│   └── PortfolioPage.tsx
├── features/                            ✅ 우수한 구조
│   └── backtest/                        (60+ files)
│       ├── api/                         - API 호출
│       ├── components/                  - UI 컴포넌트 (15개)
│       │   ├── results/                 - 결과 표시 (10개)
│       │   ├── volatility/              - 변동성 관련 (2개)
│       │   ├── shared/                  - 공유 컴포넌트 (3개)
│       │   └── lazy/                    - 지연 로딩 (1개)
│       ├── hooks/                       - 커스텀 훅 (7개)
│       ├── model/                       - 상태/타입 (15개)
│       ├── services/                    - 비즈니스 로직 (1개)
│       └── utils/                       - 유틸리티 (4개)
└── shared/                              ⚠️ 일부 중복 및 혼란
    ├── api/                             (2 files) ✅
    ├── components/                      (9 files) ⚠️ vs src/components?
    ├── config/                          (1 file) ✅
    ├── hooks/                           (5 files) ✅
    ├── lib/                             ⚠️ 복잡한 중첩
    │   ├── core/                        - utils.ts (cn 함수)
    │   └── utils/                       - 5개 유틸 파일
    ├── styles/                          (1 file) ✅
    ├── types/                           (2 files) ✅
    ├── ui/                              (17 files) ✅ shadcn/ui
    └── utils/                           (1 file) - dataSampling.ts
```

---

## ⚠️ 문제점 분석

### 1. **src/components vs src/shared/components** - 역할 중복 ⚠️⚠️⚠️

#### 현재 상황
```
src/components/           (3 files)
├── ErrorBoundary.tsx     - 전역 에러 처리
├── Header.tsx            - 전역 헤더
└── ThemeSelector.tsx     - 테마 선택 (Header에서만 사용)

src/shared/components/    (9 files)
├── FormField.tsx
├── FormSection.tsx
├── FormLegend.tsx
├── ChartLoading.tsx
├── LoadingSpinner.tsx
├── ErrorMessage.tsx
├── FinancialTermTooltip.tsx
└── PerformanceMonitor.tsx
└── index.ts
```

#### 문제점
- **명확한 구분 없음**: 둘 다 "공통 컴포넌트"를 담고 있음
- **임포트 혼란**: 개발자가 어디서 가져올지 헷갈림
- **일관성 부족**: `@/components` vs `@/shared/components`

#### 임포트 패턴 분석
```typescript
// src/components는 App.tsx에서만 사용
import Header from '@/components/Header';  // ❌ 1회만 사용

// shared/components는 features에서 광범위하게 사용
import { FormField } from '@/shared/components';  // ✅ 10+ 회 사용
```

---

### 2. **src/lib vs src/shared/lib** - 유틸리티 중복 ⚠️⚠️

#### 현재 상황
```
src/lib/utils.ts                          (Re-export만)
└── export * from '@/shared/lib/core/utils';

src/shared/lib/
├── core/
│   └── utils.ts                          (cn 함수만)
└── utils/
    ├── chartUtils.ts                     (차트 관련)
    ├── dateUtils.ts                      (날짜 관련)
    ├── formatters.ts                     (포맷팅)
    ├── numberUtils.ts                    (숫자 관련)
    └── index.ts

src/shared/utils/
└── dataSampling.ts                       (데이터 샘플링)
```

#### 문제점
- **3단계 중첩**: `lib/core/utils`, `lib/utils/`, `utils/` - 복잡함
- **Re-export 필요성**: `src/lib/utils.ts`가 단순 재수출만 함
- **분류 기준 불명확**: `lib/utils` vs `utils`의 차이가 불분명

#### 임포트 패턴 분석
```typescript
// 모든 shadcn/ui 컴포넌트가 사용
import { cn } from "@/lib/utils"  // ✅ 17회 사용 (shadcn 표준)

// features에서 직접 사용
import { formatCurrency } from '@/shared/lib/utils/formatters';  // ✅
```

---

### 3. **src/shared의 과도한 책임** ⚠️

#### 현재 포함 항목
```
src/shared/
├── api/          ✅ API 클라이언트
├── components/   ⚠️ 공통 컴포넌트 (vs src/components?)
├── config/       ✅ 설정
├── hooks/        ✅ 공통 훅
├── lib/          ⚠️ 유틸리티 (복잡한 구조)
├── styles/       ✅ 디자인 토큰
├── types/        ✅ 타입 정의
├── ui/           ✅ shadcn/ui 컴포넌트
└── utils/        ⚠️ 유틸리티 (vs lib?)
```

#### 문제점
- **단일 디렉토리에 너무 많은 역할**: 9개 하위 디렉토리
- **일부 항목 중복**: `lib` vs `utils`, `components` 역할 모호
- **인지 부하**: 개발자가 파일 위치 찾기 어려움

---

## ✅ 잘 구성된 부분

### 1. **features/backtest/** - 우수한 Feature 구조 ⭐⭐⭐⭐⭐

```
features/backtest/
├── api/              ✅ API 계층 분리
├── components/       ✅ UI 컴포넌트
│   ├── results/      ✅ 도메인별 그룹핑
│   ├── volatility/   ✅
│   └── shared/       ✅ Feature 내부 공유
├── hooks/            ✅ 비즈니스 로직 훅
├── model/            ✅ 상태 관리 + 타입
│   ├── constants/    ✅
│   └── types/        ✅
├── services/         ✅ 비즈니스 로직
└── utils/            ✅ Feature 전용 유틸
```

**장점**:
- ✅ **도메인 주도 설계**: 백테스트 관련 모든 것이 한 곳에
- ✅ **명확한 계층 분리**: API → Service → Hooks → Components
- ✅ **높은 응집도**: 관련 코드가 가까이 위치
- ✅ **낮은 결합도**: 다른 feature와 독립적

---

### 2. **src/shared/ui/** - shadcn/ui 표준 ⭐⭐⭐⭐⭐

```
src/shared/ui/
├── button.tsx        ✅ shadcn/ui 표준
├── card.tsx          ✅
├── dialog.tsx        ✅
├── input.tsx         ✅
└── ...               (17 files)
```

**장점**:
- ✅ **업계 표준**: shadcn/ui 권장 구조 준수
- ✅ **일관된 임포트**: `@/shared/ui/*`
- ✅ **자동 생성**: `npx shadcn add <component>`

---

### 3. **src/pages/** - 간단하고 명확 ⭐⭐⭐⭐

```
src/pages/
├── HomePage.tsx      ✅ 라우트 페이지
└── PortfolioPage.tsx ✅
```

**장점**:
- ✅ **명확한 역할**: 라우트 진입점
- ✅ **적절한 수**: 2개 (과하지 않음)

---

## 🎯 개선 제안

### 제안 1: **src/components 통합** (우선순위: 높음) 🔥

#### 현재
```
src/components/           (3 files)
src/shared/components/    (9 files)
```

#### 개선안 A: 모두 src/shared/components로 이동 (권장)
```
src/shared/components/
├── layout/                     (전역 레이아웃)
│   ├── ErrorBoundary.tsx      ← src/components에서 이동
│   ├── Header.tsx             ← src/components에서 이동
│   └── ThemeSelector.tsx      ← src/components에서 이동
├── form/                       (폼 관련)
│   ├── FormField.tsx
│   ├── FormSection.tsx
│   └── FormLegend.tsx
├── loading/                    (로딩 상태)
│   ├── ChartLoading.tsx
│   └── LoadingSpinner.tsx
├── feedback/                   (피드백)
│   └── ErrorMessage.tsx
├── tooltip/                    (툴팁)
│   └── FinancialTermTooltip.tsx
├── debug/                      (개발 도구)
│   └── PerformanceMonitor.tsx
└── index.ts                    (Re-exports)
```

**장점**:
- ✅ 단일 출처: 모든 공통 컴포넌트가 한 곳에
- ✅ 명확한 분류: 역할별 하위 디렉토리
- ✅ 임포트 일관성: `@/shared/components/*`

#### 개선안 B: src/components를 앱 레벨 전용으로 (대안)
```
src/components/           (앱 레벨만)
├── ErrorBoundary.tsx
├── Header.tsx
└── ThemeSelector.tsx

src/shared/components/    (재사용 가능)
└── (현재 구조 유지)
```

**판단 기준**:
- `src/components`: 앱에만 종속 (다른 프로젝트에서 재사용 불가)
- `src/shared/components`: 재사용 가능 (다른 프로젝트에도 적용 가능)

---

### 제안 2: **유틸리티 구조 단순화** (우선순위: 중간) 🔧

#### 현재 (복잡함)
```
src/lib/utils.ts                (Re-export만)
src/shared/lib/core/utils.ts    (cn 함수)
src/shared/lib/utils/           (5개 파일)
src/shared/utils/               (1개 파일)
```

#### 개선안: 플랫 구조
```
src/lib/
└── utils.ts                    (cn 함수) - shadcn 표준 유지

src/shared/utils/               (모든 유틸리티)
├── cn.ts                       (또는 lib/utils.ts와 동일)
├── chartUtils.ts
├── dateUtils.ts
├── formatters.ts
├── numberUtils.ts
├── dataSampling.ts
└── index.ts                    (Re-exports)
```

**또는 카테고리별 분류**:
```
src/shared/utils/
├── dom/                        (DOM 관련)
│   └── cn.ts
├── chart/                      (차트 관련)
│   └── chartUtils.ts
├── date/                       (날짜 관련)
│   └── dateUtils.ts
├── number/                     (숫자 관련)
│   ├── formatters.ts
│   └── numberUtils.ts
├── data/                       (데이터 처리)
│   └── dataSampling.ts
└── index.ts
```

**trade-off**:
- **플랫 구조**: 간단하지만 파일 증가 시 복잡해질 수 있음
- **카테고리 구조**: 명확하지만 작은 프로젝트에는 과도할 수 있음

---

### 제안 3: **src/lib/utils.ts 제거** (우선순위: 낮음)

#### 현재
```typescript
// src/lib/utils.ts
export * from '@/shared/lib/core/utils';
```

#### 개선안: 직접 임포트
```typescript
// Before
import { cn } from "@/lib/utils"

// After
import { cn } from "@/shared/utils"
// 또는
import { cn } from "@/shared/lib/utils"
```

**문제점**:
- ❌ **Breaking Change**: shadcn/ui 표준에서 벗어남
- ❌ **17개 파일 수정 필요**: 모든 UI 컴포넌트 임포트 변경

**권장**: **유지** (shadcn 표준 준수)

---

## 📋 우선순위별 개선 로드맵

### Phase 1: 즉시 개선 (Breaking Changes 없음)

#### 1.1 문서화
```markdown
# 디렉토리 규칙 (README.md에 추가)

- `src/components/`: 앱 레벨 전역 컴포넌트 (ErrorBoundary, Header)
- `src/shared/components/`: 재사용 가능한 공통 컴포넌트
- `src/lib/utils.ts`: shadcn/ui 표준 (cn 함수)
- `src/shared/lib/utils/`: 범용 유틸리티
- `src/features/*/`: Feature별 독립적 모듈
```

#### 1.2 린트 규칙 추가
```typescript
// .eslintrc.js
rules: {
  'no-restricted-imports': [
    'error',
    {
      patterns: [
        {
          group: ['../../../*'],  // 3단계 이상 상대 경로 금지
          message: '절대 경로(@/)를 사용하세요.'
        }
      ]
    }
  ]
}
```

---

### Phase 2: 점진적 개선 (신규 파일부터)

#### 2.1 신규 컴포넌트 위치 규칙
```
✅ 앱 레벨 전역 → src/components/
✅ 재사용 가능 공통 → src/shared/components/
✅ Feature 전용 → src/features/*/components/
```

#### 2.2 신규 유틸리티 위치 규칙
```
✅ DOM 조작 (cn 등) → src/lib/utils.ts (shadcn 표준)
✅ 범용 유틸 → src/shared/utils/
✅ Feature 전용 → src/features/*/utils/
```

---

### Phase 3: 대규모 리팩토링 (선택 사항)

#### 3.1 src/components 통합 (Breaking Changes)
```bash
# 1. 파일 이동
mv src/components/*.tsx src/shared/components/layout/

# 2. 임포트 수정 (1개 파일만)
# src/App.tsx
- import Header from '@/components/Header';
+ import { Header } from '@/shared/components/layout';

# 3. src/components 디렉토리 삭제
rm -rf src/components
```

**영향도**: 낮음 (1개 파일만 수정)

#### 3.2 유틸리티 플랫화 (선택)
```bash
# shared/lib/utils/* → shared/utils/로 이동
mv src/shared/lib/utils/*.ts src/shared/utils/
rm -rf src/shared/lib/
```

**영향도**: 중간 (10+ 파일 임포트 수정)

---

## 🎯 최종 권장 사항

### 현재 상태 평가: **B+ (양호)**

**강점**:
- ✅ features/backtest 구조 우수
- ✅ shadcn/ui 표준 준수
- ✅ 명확한 페이지 구조

**약점**:
- ⚠️ components 역할 중복
- ⚠️ 유틸리티 중첩 복잡
- ⚠️ shared 디렉토리 과부하

---

### 즉시 실행 권장 (Breaking Changes 없음)

#### 1. **문서화 추가** (5분)
```bash
cat >> README.md << 'EOF'

## 📁 디렉토리 구조 규칙

### 컴포넌트
- `src/components/`: 앱 레벨 전역 (ErrorBoundary, Header)
- `src/shared/components/`: 재사용 가능한 공통 컴포넌트
- `src/shared/ui/`: shadcn/ui 컴포넌트
- `src/features/*/components/`: Feature 전용

### 유틸리티
- `src/lib/utils.ts`: shadcn/ui 표준 (cn 함수)
- `src/shared/lib/utils/`: 범용 유틸리티
- `src/features/*/utils/`: Feature 전용

### 임포트 규칙
- 항상 절대 경로 사용: `@/shared/...`
- 3단계 이상 상대 경로 금지: `../../../` ❌
EOF
```

#### 2. **ARCHITECTURE.md 생성** (참고용)
이미 이 파일(CODEBASE_STRUCTURE_ANALYSIS.md)이 그 역할을 함!

---

### 향후 개선 (선택 사항)

#### Phase 1: 문서화 (완료 ✅)
- [x] 디렉토리 규칙 문서화
- [x] 구조 분석 리포트 작성

#### Phase 2: 점진적 개선 (신규 코드부터)
- [ ] 신규 컴포넌트 위치 규칙 준수
- [ ] 신규 유틸리티 위치 규칙 준수
- [ ] 린트 규칙 추가

#### Phase 3: 대규모 리팩토링 (졸업 후)
- [ ] src/components 통합 검토
- [ ] 유틸리티 구조 단순화 검토

---

## 🎓 교수님께 어필 포인트

### 1. **Feature-First Architecture** ⭐⭐⭐⭐⭐
> "features/backtest 디렉토리를 통해 도메인 주도 설계를 적용하여 높은 응집도와 낮은 결합도를 달성했습니다."

### 2. **shadcn/ui 표준 준수** ⭐⭐⭐⭐⭐
> "업계 표준인 shadcn/ui의 권장 구조를 따라 일관성 있는 UI 컴포넌트 시스템을 구축했습니다."

### 3. **명확한 계층 분리** ⭐⭐⭐⭐
> "API → Service → Hooks → Components 계층을 명확히 분리하여 유지보수성을 높였습니다."

### 4. **개선 여지 인식** ⭐⭐⭐⭐
> "현재 구조의 문제점(components 중복, 유틸리티 중첩)을 분석하고 개선 방안을 수립했습니다."

---

## 📊 구조 비교: Before → After (향후)

### 현재 (B+)
```
src/
├── components/        ⚠️ 역할 모호 (3 files)
├── lib/               ⚠️ Re-export만 (1 file)
├── shared/
│   ├── components/    ⚠️ vs src/components?
│   ├── lib/           ⚠️ 3단계 중첩
│   └── utils/         ⚠️ vs lib?
└── features/          ✅ 우수 (60+ files)
```

### 개선 후 (A)
```
src/
├── components/        ✅ 앱 레벨만 (또는 제거)
├── lib/               ✅ shadcn 표준 유지
├── shared/
│   ├── components/    ✅ 명확한 분류
│   │   ├── layout/
│   │   ├── form/
│   │   └── loading/
│   └── utils/         ✅ 플랫 구조
└── features/          ✅ 유지
```

---

## 🎉 결론

### 현재 평가: **B+ (양호)**

**핵심 요약**:
1. ✅ **features/backtest**: 우수한 Feature 구조
2. ✅ **shared/ui**: shadcn/ui 표준 준수
3. ⚠️ **components 중복**: 역할 정리 필요
4. ⚠️ **유틸리티 중첩**: 단순화 권장

**졸업작품 수준**: **충분히 우수** ✅
- 대부분의 구조가 논리적이고 확장 가능
- 일부 중복은 점진적 개선 가능
- 교수님께 구조 설계 능력 충분히 어필 가능

**즉시 실행**: 문서화만 추가 (5분) ✅  
**향후 개선**: 선택 사항 (졸업 후 리팩토링)

---

**작성일**: 2025-11-10  
**버전**: v1.6.10  
**프로젝트**: 라고할때살걸 (Backtest Platform)
