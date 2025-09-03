# 프론트엔드 개발 가이드

React 18 + TypeScript 기반의 백테스팅 웹 애플리케이션 개발 가이드입니다.

## 기술 스택

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **UI Framework**: React Bootstrap + Bootstrap 5
- **Charting**: Recharts
- **Testing**: Vitest + Testing Library
- **Container**: Docker

## 프로젝트 구조

```
frontend/
├── src/
│   ├── components/           # React 컴포넌트
│   │   ├── UnifiedBacktestForm.tsx  # 통합 백테스트 폼
│   │   ├── BacktestResult.tsx       # 백테스트 결과 표시
│   │   ├── ErrorBoundary.tsx        # 에러 경계 컴포넌트
│   │   └── ServerStatus.tsx         # 서버 상태 표시
│   ├── pages/              # 페이지 컴포넌트
│   ├── services/            # API 호출 서비스
│   │   └── api.ts          # 백엔드 API 호출 함수
│   ├── types/              # TypeScript 타입 정의
│   │   └── api.ts          # API 관련 타입
│   ├── constants/          # 상수 정의
│   │   └── strategies.ts   # 전략 및 종목 상수
│   ├── utils/              # 유틸리티 함수
│   │   └── formatters.ts   # 데이터 포맷팅 함수
│   ├── hooks/              # 커스텀 훅 (향후 확장)
│   └── test/               # 테스트 파일
├── doc/                    # 문서
└── public/                 # 정적 파일
```

## 주요 컴포넌트

### UnifiedBacktestForm
- **역할**: 백테스트 설정 및 실행을 위한 통합 폼
- **특징**: 단일 종목과 포트폴리오 백테스트 모두 지원
- **현금 자산**: asset_type 필드로 현금과 주식 구분

### BacktestResult
- **역할**: 백테스트 결과 시각화 및 표시
- **차트**: Recharts를 사용한 수익률 차트, OHLC 차트
- **통계**: 총 수익률, 샤프 비율, 최대 손실폭 등

### ErrorBoundary
- **역할**: React 에러 포착 및 사용자 친화적 에러 표시
- **적용 범위**: 전체 애플리케이션

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

### 디버깅 도구
- **React DevTools**: 컴포넌트 상태 및 props 확인
- **Browser DevTools**: 네트워크 요청 및 콘솔 에러 확인
- **Vite DevTools**: 빌드 과정 및 모듈 의존성 확인

## 향후 개선 계획

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

## 문서 구조

- [API 통신 가이드](./API_GUIDE.md) - REST API 호출 및 에러 처리
- [컴포넌트 아키텍처](./COMPONENTS.md) - React 컴포넌트 설계 및 재사용
- [상태 관리 가이드](./STATE_MANAGEMENT.md) - useState, useReducer, Context API 패턴