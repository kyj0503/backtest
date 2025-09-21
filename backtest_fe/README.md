# 백테스팅 프론트엔드 (backtest_fe)

React + Vite + TypeScript 기반 백테스팅 대시보드 애플리케이션입니다.

## 빠른 시작
```bash
# 로컬 개발
npm ci
npm run dev

# Docker Compose (개발)
docker compose -f compose.yaml up --build frontend-dev
```

## 기술 스택
- React 18, TypeScript, Vite
- Tailwind CSS, shadcn/ui (Radix UI)
- React Router, Recharts

## 주요 기능
- 백테스팅 결과 시각화
- 포트폴리오 분석 대시보드
- 다크/라이트 모드 및 테마 시스템
- 반응형 디자인

## 환경변수
- `VITE_API_BASE_URL`: 백엔드 API 주소 (기본값: 상대 경로 `/api`, 예: `http://localhost:8080/api`)
- `API_PROXY_TARGET`: 개발 서버 프록시 타겟 (기본값: `http://localhost:8080`)

## 문서
자세한 내용은 [`docs/`](./docs/) 디렉터리를 참조하세요.
