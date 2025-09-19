# 01. 프론트엔드 문서 개요 (backtest_fe)

이 디렉터리는 프론트엔드(React + Vite + TypeScript + Tailwind + shadcn/ui) 관련 문서를 모아둔 장소입니다. 실제 코드와 스크립트에 맞춰 작성되어 있으며, 빠르게 개발 환경을 세팅하고 구조를 이해하는 데 목적이 있습니다.

## 기술 스택
- React 18, TypeScript, Vite 4
- Tailwind CSS, shadcn/ui(Radix UI 기반), lucide-react
- 라우팅: `react-router-dom`
- 차트: `recharts`

## 실행 스크립트 (package.json)
- 개발 서버: `npm run dev` (Vite, 기본 포트 `5173`)
- 프로덕션 빌드: `npm run build`
- 프리뷰 서버: `npm run preview`
- 린트: `npm run lint` / 자동수정 `npm run lint:fix`
- 타입 체크: `npm run type-check`

## 디렉터리 개요 (`src/`)
- `components/`: 페이지 비종속 재사용 컴포넌트
- `features/`: 도메인/기능 단위 모듈(예: `auth`, `backtest`, `community`)
- `pages/`: 라우팅되는 페이지 컴포넌트
- `shared/`: 공통 UI, hooks, api 유틸, 타입 정의
- `themes/`: JSON 기반 테마 정의

## 환경변수
- `.env` (로컬), 예시는 `.env.example` 참조
- `VITE_API_BASE_URL`: 절대 주소 기반 API 호출을 원할 때 설정합니다. 미설정 시 상대 경로(`/api`)로 호출하며 Vite 개발 프록시가 적용됩니다.
- 개발 프록시 타겟은 `vite.config.ts`의 `API_PROXY_TARGET` 환경변수로 제어합니다(기본값 `http://localhost:8001`).
- HMR 이슈가 있을 경우 `DISABLE_HMR=1 npm run dev`로 HMR을 비활성화할 수 있습니다.

## 경로 별칭
- `@` → `./src`

## 문서 색인
- 02. 개발 가이드: `./DEVELOPMENT_GUIDE.md`
- 03. 테마 시스템: `./THEME_SYSTEM.md`
