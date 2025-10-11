# Backtest Frontend

백테스트 플랫폼의 React 기반 프론트엔드 애플리케이션입니다.

## 프로젝트 개요

트레이딩 전략의 백테스팅과 포트폴리오 최적화를 위한 웹 인터페이스입니다.

**주요 기능:**
- 백테스트 실행 및 결과 시각화
- 전략 매개변수 최적화
- 포트폴리오 구성 및 분석
- 실시간 데이터 조회
- 테마 커스터마이징

## 기술 스택

- **프레임워크**: React 18.2, TypeScript 5.0
- **빌드 도구**: Vite 4.4
- **스타일링**: Tailwind CSS, shadcn/ui
- **상태 관리**: Custom Hooks (useAsync, useForm)
- **차트**: Recharts
- **HTTP 클라이언트**: Axios
- **테스트**: Vitest, Testing Library, MSW
- **환경**: Node.js >=20.0.0

## 빠른 시작

### 로컬 환경

```bash
# 의존성 설치
npm ci

# 환경 변수 설정 (선택사항)
cp .env.example .env

# 개발 서버 실행
npm run dev

# 접속: http://localhost:5173
```

### Docker 환경

```bash
# 프로젝트 루트에서 실행
cd /path/to/backtest

# 컨테이너 시작
docker compose -f compose.dev.yaml up -d backtest_fe

# 로그 확인
docker compose -f compose.dev.yaml logs -f backtest_fe

# 접속: http://localhost:5173
```

## 주요 스크립트

```bash
# 개발
npm run dev          # 개발 서버 실행 (포트 5173)
npm run build        # 프로덕션 빌드
npm run preview      # 빌드 결과 미리보기

# 테스트
npm test             # 테스트 실행 (watch 모드)
npm run test:run     # 단일 실행 (CI 모드)
npm run test:coverage # 커버리지 리포트
npm run test:ui      # Vitest UI 모드

# 코드 품질
npm run lint         # ESLint 검사
npm run lint:fix     # ESLint 자동 수정
npm run type-check   # TypeScript 타입 검사
```

## 디렉터리 구조

```
src/
├── shared/                 # 공통 인프라
│   ├── types/             # 글로벌 타입 정의
│   ├── config/            # 환경 설정
│   ├── hooks/             # 재사용 가능한 훅
│   ├── utils/             # 유틸리티 함수들
│   ├── ui/                # shadcn/ui 컴포넌트
│   └── components/        # 공통 컴포넌트
├── features/              # 기능별 모듈
│   ├── backtest/         # 백테스트 기능
│   └── shared/           # 공통 기능(필요 시 분리)
├── pages/                # 페이지 컴포넌트
├── test/                 # 테스트 유틸리티
└── themes/               # 테마 정의 파일
```

## 환경 변수

루트 `.env.local` 예시는 다음과 같습니다.

```bash
VITE_API_BASE_URL=/api
API_PROXY_TARGET=http://backtest_be_fast:8000
FASTAPI_PROXY_TARGET=http://backtest_be_fast:8000
VITE_APP_VERSION=1.0.0
```

## 프록시 설정

개발 중 CORS 문제 해결을 위한 프록시가 구성되어 있습니다 (vite.config.ts):

- `/api/v1/backtest` → FastAPI (포트 8000)

## 테스트

### 현재 테스트 현황

```
Test Files:  6
Tests:       59
Duration:    약 2초 (vitest run 기준)
```

테스트 분포는 다음과 같습니다.
- 공용 훅 및 유틸리티 단위 테스트: 33개
- 서비스 레이어 단위 테스트: 10개 (axios 클라이언트를 목킹)
- UI 컴포넌트 테스트: 16개 (Testing Library 기반)

### 테스트 실행

```bash
# 로컬 환경
npm run test:run

# Docker 환경
docker compose -f compose.dev.yaml exec backtest_fe npm run test:run
```

테스트 작성 규칙과 목록은 `docs/Test.md`에 정리되어 있다.

## 빌드 및 배포

### 프로덕션 빌드

```bash
# 타입 체크
npm run type-check

# 린팅
npm run lint

# 테스트
npm run test:run

# 빌드
npm run build
```

빌드 결과는 `dist/` 디렉터리에 생성됩니다.

### Docker 빌드

```bash
# 개발 이미지
docker build -f Dockerfile.dev -t backtest-fe:dev .

# 프로덕션 이미지
docker build -f Dockerfile -t backtest-fe:prod .
```

## 코드 품질

### ESLint 규칙

- TypeScript 권장 규칙 적용
- React Hooks 규칙 적용
- 미사용 변수 오류 처리
- 명시적 any 타입 오류 처리

### TypeScript 설정

- Strict 모드 활성화
- Path alias 설정 (`@/*`)
- ES Module 사용

## 주요 의존성

**프로덕션 의존성:**
- react: ^18.2.0
- react-dom: ^18.2.0
- react-router-dom: ^6.30.1
- axios: ^1.6.0
- recharts: ^2.9.0
- zod: ^3.25.76
- react-hook-form: ^7.62.0
- lucide-react: ^0.544.0

**개발 의존성:**
- typescript: ^5.0.0
- vite: ^4.4.0
- vitest: ^3.2.4
- @testing-library/react: ^16.3.0
- msw: ^2.11.3
- happy-dom: ^16.14.4
- tailwindcss: ^3.3.0
