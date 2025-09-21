# 프론트엔드 개요

## 📱 개요

전문적인 백테스팅 플랫폼의 프론트엔드 애플리케이션입니다. 최신 React 생태계와 TypeScript를 기반으로 구축되었으며, 실무 수준의 아키텍처와 개발 경험을 제공합니다.

## 🚀 기술 스택

### 핵심 기술
- **React 18.2+** - 최신 React 기능 활용
- **TypeScript 5.0+** - 타입 안전성과 개발 생산성
- **Vite 4.4+** - 빠른 빌드와 HMR

### UI/UX
- **Tailwind CSS** - 유틸리티 기반 스타일링
- **shadcn/ui** - 접근성 고려 컴포넌트 라이브러리
- **Recharts** - 데이터 시각화
- **Lucide React** - 일관된 아이콘 시스템

### 개발 도구
- **Vitest** - 빠른 단위 테스트
- **Testing Library** - 사용자 중심 테스트
- **ESLint + TypeScript** - 코드 품질 관리

## 🏗️ 아키텍처 개요

### 폴더 구조
```
src/
├── shared/          # 공통 인프라
│   ├── types/       # 전역 타입 정의
│   ├── config/      # 환경 설정
│   ├── hooks/       # 재사용 가능한 훅
│   ├── utils/       # 유틸리티 함수
│   └── components/  # 공통 컴포넌트
├── features/        # 기능별 모듈
│   ├── backtest/    # 백테스트 기능
│   ├── portfolio/   # 포트폴리오 관리
│   └── auth/        # 인증 관련
├── pages/           # 페이지 컴포넌트
└── test/            # 테스트 유틸리티
```

### 핵심 원칙
- **관심사 분리**: 기능별 모듈화
- **타입 안전성**: 전체 애플리케이션 TypeScript 적용
- **재사용성**: 공통 인프라와 커스텀 훅
- **테스트 가능성**: 종합적인 테스트 전략

## ⚡ 빠른 시작

```bash
# 의존성 설치
npm ci

# 환경 설정
cp .env.example .env

# 개발 서버 실행
npm run dev

# 브라우저에서 확인
# http://localhost:5173
```

## 🔧 주요 스크립트

```bash
# 개발
npm run dev          # 개발 서버 실행
npm run build        # 프로덕션 빌드
npm run preview      # 빌드 결과 미리보기

# 테스트
npm run test         # 테스트 실행 (watch 모드)
npm run test:run     # 단일 실행
npm run test:coverage # 커버리지 리포트

# 코드 품질
npm run lint         # ESLint 검사
npm run lint:fix     # ESLint 자동 수정
npm run type-check   # TypeScript 타입 검사
```

## 🌐 환경 변수

### 개발 환경
```bash
VITE_API_URL=http://localhost:8080/api
VITE_ENVIRONMENT=development
VITE_DEBUG=true
```

### 프로덕션 환경
```bash
VITE_API_URL=https://api.backtest.com/api
VITE_ENVIRONMENT=production
VITE_DEBUG=false
```

## 📚 문서 가이드

| 문서 | 설명 |
|------|------|
| [Architecture.md](./Architecture.md) | 상세 아키텍처 가이드 |
| [Development.md](./Development.md) | 개발 규칙과 패턴 |
| [Deployment.md](./Deployment.md) | 배포 및 운영 가이드 |
| [Theme.md](./03-Theme.md) | 테마 시스템 사용법 |

## 🤝 기여하기

1. **코딩 스타일**: ESLint 규칙 준수
2. **테스트**: 새로운 기능에 테스트 포함
3. **타입 안전성**: any 타입 사용 금지
4. **문서화**: 복잡한 로직에 주석 추가

## 📝 주요 기능

- ✅ **백테스트 실행**: 다양한 전략으로 백테스트 수행
- ✅ **결과 시각화**: 상세한 차트와 메트릭
- ✅ **포트폴리오 관리**: 자산 배분 및 리밸런싱
- ✅ **성능 분석**: 수익률, 샤프 비율 등 지표
- ✅ **반응형 디자인**: 모바일 친화적 UI
- ✅ **다크 모드**: 사용자 선호도 지원

## 🔗 관련 서비스

- **Backend (FastAPI)**: `/backtest_be_fast` - 백테스트 엔진
- **Backend (Spring)**: `/backtest_be_spring` - 사용자 관리, 채팅
- **Database**: MySQL 8.0+
- **Cache**: Redis (선택사항)