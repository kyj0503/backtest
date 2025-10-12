# 프론트엔드 테스트 가이드

## 테스트 실행

**로컬:**
```bash
cd backtest_fe
npm run test:run
```

**커버리지:**
```bash
npm run test:coverage
```

**Docker:**
```bash
docker compose -f compose.dev.yaml exec backtest_fe npm run test:run
```

## 테스트 위치

- `src/components/__tests__`: UI 컴포넌트
- `src/shared/hooks/__tests__`: 공통 훅
- `src/features/backtest/hooks/__tests__`: 백테스트 훅
- `src/features/backtest/services/__tests__`: API 서비스

## 테스트 도구

- **프레임워크**: Vitest
- **렌더링**: React Testing Library
- **API 모킹**: MSW (Mock Service Worker)
