# 02. 개발 가이드 — 프론트엔드

요구 사항
- Node.js 18+ 권장

빠른 시작
```bash
cd backtest_fe
npm ci
npm run dev
```

빌드/프리뷰
```bash
npm run build
npm run preview
```

환경변수
- `.env.example` 참고: `VITE_API_BASE_URL`, `DISABLE_HMR`
- 스프링 백엔드와 연결 시 `VITE_API_BASE_URL=http://localhost:8080/api`, `API_PROXY_TARGET=http://localhost:8080` 조합을 권장합니다.

프록시
- 개발 서버 프록시는 `vite.config.ts`의 `API_PROXY_TARGET`을 사용하여 `/api` 경로를 포워딩합니다.
