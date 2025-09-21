# 백테스팅 프론트엔드

> 최신 React, TypeScript, Tailwind CSS를 활용한 전문적인 백테스팅 대시보드

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/your-repo/backtest-frontend)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.2+-61dafb)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-4.4+-646cff)](https://vitejs.dev/)

## 🚀 주요 기능

- **고성능 백테스팅**: 단일 종목 및 포트폴리오 백테스트 지원
- **인터랙티브 차트**: Recharts 기반 실시간 데이터 시각화
- **다양한 전략**: 이동평균, RSI, 볼린저 밴드 등 다양한 트레이딩 전략
- **실시간 데이터**: Yahoo Finance API 연동으로 최신 시장 데이터 제공
- **포트폴리오 관리**: 자산 배분 및 리밸런싱 시뮬레이션
- **위험 분석**: VaR, CVaR, 샤프비율 등 위험 지표 제공
- **테마 시스템**: 다크/라이트 모드 및 커스텀 테마 지원
- **반응형 디자인**: 모바일부터 데스크톱까지 완벽한 반응형 UI

## 🛠️ 설치 및 실행

### 필수 요구사항

- Node.js 16.0.0 이상
- npm 8.0.0 이상

### 개발 환경 설정

```bash
# 의존성 설치
npm ci

# 환경 변수 설정
cp .env.example .env

# 개발 서버 실행
npm run dev
```

### Docker로 실행

```bash
# 개발 환경
docker compose -f compose/compose.dev.yaml up -d

# 프로덕션 환경
docker compose -f compose/compose.prod.yaml up -d
```

## 🏗️ 아키텍처

### 프로젝트 구조

```
src/
├── shared/                 # 공통 모듈
│   ├── api/               # API 클라이언트 및 인터셉터
│   ├── config/            # 환경 설정
│   ├── hooks/             # 재사용 가능한 커스텀 훅
│   ├── types/             # 전역 타입 정의
│   ├── ui/                # shadcn/ui 컴포넌트
│   └── utils/             # 유틸리티 함수
├── features/              # 기능별 모듈
│   ├── auth/              # 인증 관련
│   ├── backtest/          # 백테스트 기능
│   ├── chat/              # 실시간 채팅
│   └── community/         # 커뮤니티 기능
├── pages/                 # 페이지 컴포넌트
├── components/            # 공통 컴포넌트
└── test/                  # 테스트 유틸리티
```

### 기술 스택

- **프레임워크**: React 18.2+ with TypeScript
- **빌드 도구**: Vite 4.4+
- **스타일링**: Tailwind CSS + shadcn/ui
- **상태 관리**: React Context + Custom Hooks
- **차트**: Recharts 2.9+
- **HTTP 클라이언트**: Axios
- **테스트**: Vitest + Testing Library
- **코드 품질**: ESLint + TypeScript

## 🧪 테스트

```bash
# 단위 테스트 실행
npm run test

# 테스트 실행 (CI 모드)
npm run test:run

# 커버리지 리포트
npm run test:coverage

# 테스트 UI
npm run test:ui
```

## 📊 환경 변수

```env
# API 설정
VITE_API_BASE_URL=/api           # 백엔드 API 주소
API_PROXY_TARGET=http://localhost:8080  # 개발 서버 프록시 타겟

# 앱 정보
VITE_APP_VERSION=1.0.0
VITE_BUILD_TIME=2024-01-01T00:00:00Z
```

## 🎨 개발 가이드

### 커스텀 훅 사용

```typescript
import { useBacktest } from '@/features/backtest/hooks/useBacktestV2'
import { useForm } from '@/shared/hooks/useForm'

// 백테스트 실행
const { runBacktest, result, isLoading } = useBacktest()

// 폼 상태 관리
const { data, setFieldValue, handleSubmit, isValid } = useForm(
  initialData, 
  validationRules
)
```

### API 서비스 사용

```typescript
import { BacktestService } from '@/features/backtest/services/backtestService'

// 백테스트 실행
const result = await BacktestService.executeBacktest(request)

// 전략 목록 조회
const strategies = await BacktestService.getStrategies()
```

## 📖 문서

- [개발 가이드](./docs/02-Development.md)
- [테마 시스템](./docs/03-Theme.md)
- [API 문서](../docs/API.md)

## 🤝 기여하기

1. 저장소를 포크합니다
2. 기능 브랜치를 생성합니다 (`git checkout -b feature/amazing-feature`)
3. 변경사항을 커밋합니다 (`git commit -m 'feat: Add amazing feature'`)
4. 브랜치에 푸시합니다 (`git push origin feature/amazing-feature`)
5. Pull Request를 생성합니다

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
