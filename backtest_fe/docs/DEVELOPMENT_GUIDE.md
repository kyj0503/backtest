# 02. 개발 가이드 — Frontend (React + Vite + Tailwind + shadcn/ui)

## 요구 사항
- Node.js 18+ (권장 20+)
- npm

## 빠른 시작
```bash
cd backtest_fe
npm ci
npm run dev
```

- 개발 서버는 기본 포트 `5173`에서 실행됩니다.
- API 호출은 기본적으로 상대 경로(`/api`)를 사용하며, Vite 프록시가 `API_PROXY_TARGET`(기본 `http://localhost:8001`)로 전달합니다.

## 빌드/프리뷰/품질 검사
```bash
# 프로덕션 빌드
npm run build

# 프리뷰 서버
npm run preview

# 린트 및 자동수정
npm run lint
npm run lint:fix

# 타입 체크만 수행
npm run type-check
```

## 환경변수
- `.env.example`를 참고하여 `.env` 파일을 생성합니다.
- `VITE_API_BASE_URL`을 설정하면 절대 경로로 API를 호출합니다. 미설정 시 상대 경로(`/api`).
- `DISABLE_HMR=1`로 HMR을 끌 수 있습니다.

예시:
```bash
# .env (로컬 개발)
# VITE_API_BASE_URL=http://localhost:8001
# DISABLE_HMR=1
```

## 경로 별칭
- `@` → `./src`
- 예: `import { Button } from '@/shared/ui/button'`

## 공통 API 유틸
- 파일: `src/shared/api/base.ts`
- `buildApiUrl(path: string)`를 사용해 API URL을 구성합니다. 내부적으로 `VITE_API_BASE_URL`을 고려합니다.

## UI 컴포넌트와 디자인 시스템
- `shadcn/ui` 기반 공용 컴포넌트는 `src/shared/ui` 아래에 있습니다.
- 비즈니스 무관 공통 컴포넌트는 `src/shared/components`에 정리되어 있습니다.
- 기능/도메인별 UI는 `src/features/**/components`에 위치합니다.

## 테마 시스템
- JSON 테마는 `src/themes/`에 위치하며, 훅 `src/shared/hooks/useTheme.ts`가 적용/저장을 담당합니다.
- 자세한 사용법은 `THEME_SYSTEM.md` 문서를 참조합니다.

## 테스트
- 테스트 스크립트는 현재 비활성화되어 있습니다. 필요 시 Vitest/Jest 도입 후 `scripts`에 `test` 명령을 추가하고 문서를 갱신하세요.

## 트러블슈팅
- HMR이 작동하지 않거나 프록시 환경에서 WebSocket이 차단될 경우: `DISABLE_HMR=1 npm run dev`
- API 404/네트워크 오류: `vite.config.ts`의 `server.proxy['/api']` 설정 및 백엔드 주소(`API_PROXY_TARGET`, `VITE_API_BASE_URL`)를 확인하세요.
