# Forms Components Directory

이 디렉토리는 백테스트 설정 폼 컴포넌트들을 관리합니다.

## 디렉토리 구조

```
forms/
├── CommissionForm.tsx          # 수수료 및 리밸런싱 설정
├── DateRangeForm.tsx           # 백테스트 기간 설정
├── StrategyForm.tsx            # 투자 전략 선택 및 파라미터
├── PortfolioForm/              # 포트폴리오 구성 (복잡하여 별도 폴더)
│   ├── index.tsx
│   ├── PortfolioTable.tsx
│   ├── PortfolioRow.tsx
│   └── DcaPreview.tsx
└── README.md                   # 이 파일
```

## 마이그레이션 가이드

### 현재 상태
현재 폼 컴포넌트들은 `components/` 루트에 있습니다.

### 향후 이동 계획

#### forms/ 폴더로 이동 예정
- `CommissionForm.tsx` ← `components/CommissionForm.tsx`
- `DateRangeForm.tsx` ← `components/DateRangeForm.tsx`
- `StrategyForm.tsx` ← `components/StrategyForm.tsx`
- `PortfolioForm.tsx` ← `components/PortfolioForm.tsx` (향후 모듈화 가능)

### PortfolioForm 모듈화 제안

`PortfolioForm.tsx`는 334줄로 큰 파일입니다. 다음과 같이 분리할 수 있습니다:

```tsx
PortfolioForm/
├── index.tsx                   // 메인 컴포넌트 (100줄)
├── PortfolioTable.tsx          // 테이블 UI (100줄)
├── PortfolioRow.tsx            // 개별 행 (100줄)
└── DcaPreview.tsx              // DCA 프리뷰 (30줄)
```

## 사용 예시

```tsx
// 폼 컴포넌트 사용
import { CommissionForm, DateRangeForm, StrategyForm } from '@/features/backtest/components/forms';

// 포트폴리오 폼 사용
import PortfolioForm from '@/features/backtest/components/forms/PortfolioForm';
```

## 장점

1. **관심사 분리**: 폼 관련 로직이 한 곳에 모입니다.
2. **쉬운 탐색**: 모든 설정 폼을 한 곳에서 관리합니다.
3. **재사용성**: 폼 컴포넌트를 다른 페이지에서도 쉽게 재사용할 수 있습니다.
4. **유지보수**: 폼 관련 수정이 필요할 때 찾기 쉽습니다.
