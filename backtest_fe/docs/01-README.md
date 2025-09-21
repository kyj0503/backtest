# 01. 프론트엔드 개요 (backtest_fe)

개요
- Vite + React + TypeScript 기반의 백테스팅 대시보드 프론트엔드입니다.

기술 스택
- React 18, TypeScript, Vite
- Tailwind CSS, shadcn/ui, Recharts

빠른 시작
```bash
cd backtest_fe
npm ci
npm run dev
```

환경변수(주요)
- `VITE_API_BASE_URL`: 백엔드 API 절대 경로 사용 시 설정 (예: `http://localhost:8080/api`)
- `API_PROXY_TARGET`: 개발 프록시 타겟(예: `http://localhost:8080`)

디렉터리 개요
- `src/` - 애플리케이션 소스
- `src/shared/` - 공용 컴포넌트, 훅, API 유틸
- `src/themes/` - JSON 테마 파일

문서 색인
- 02-Development.md — 개발 가이드 및 스크립트 설명
- 03-Theme.md — 테마 시스템 및 사용법
