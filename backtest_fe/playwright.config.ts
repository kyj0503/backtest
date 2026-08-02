import { defineConfig, devices } from '@playwright/test';

// P2-38: 이 config는 사람이 의도적으로 돌리는 스모크 테스트 전용이다.
// Jenkinsfile의 Quality Gate에는 연결하지 않았다 - 그 게이트는
// `docker build --target test`로 도는 순수 컨테이너 빌드라 브라우저도,
// 살아있는 백엔드도 없다 (docker build로는 실행 불가능한 테스트를 CI에
// 연결해봐야 "항상 통과"하거나 "항상 실패"하는 무의미한 스텝이 될 뿐이다).
//
// webServer를 의도적으로 두지 않았다: FE(:5173)/BE(:8000)는 이미 떠 있는
// 개발 스택(`docker compose -f compose.dev.yaml up -d`)을 그대로 사용한다.
// Playwright가 자체적으로 별도 vite 인스턴스를 띄우면 이미 실행 중인 dev
// 컨테이너와 포트가 충돌하거나, FASTAPI_PROXY_TARGET 등 컨테이너 네트워크
// 전용 프록시 설정 없이 뜬 인스턴스가 /api/v1/backtest를 BE로 전달하지
// 못해 오히려 신뢰할 수 없는 테스트가 된다. 실행 전 FE/BE가 떠 있는지는
// spec의 global setup이 아니라 사람이 `docker compose ps`로 직접 확인한다.
export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  retries: 0,
  // 백테스트 스모크 테스트는 실제 백엔드 실행(yfinance 조회 포함)을 기다려야
  // 한다. client.ts의 BACKTEST_REQUEST_TIMEOUT_MS(axios 자체 타임아웃)가
  // 185_000ms이므로, 그보다 여유 있게 잡는다.
  timeout: 220_000,
  expect: {
    timeout: 10_000,
  },
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
