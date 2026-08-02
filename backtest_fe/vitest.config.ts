import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    pool: 'forks',
    // Vitest 4: poolOptions 제거됨. singleFork: true === maxWorkers: 1 + isolate: false
    maxWorkers: 1,
    // isolate: false는 쓰지 않는다.
    //
    // 모든 테스트 파일이 하나의 happy-dom 환경을 공유하게 되는데, vitest는
    // 직전 실행 소요시간을 캐시해 파일 실행 순서를 조정하므로 순서가 실행마다
    // 바뀐다. 그 결과 스위트가 flaky해진다 — 같은 커밋에서 113 passed와
    // 3 failed가 번갈아 나오는 것을 확인했다(routing / ThemeSelector /
    // backtestService.integration, 최대 9건까지 실패).
    // 격리 비용보다 결과를 믿을 수 있는 편이 중요하다.
    isolate: true,
    sequence: {
      concurrent: false,
    },
    exclude: [
      '**/node_modules/**',
      '**/dist/**',
      '**/e2e/**',  // E2E 테스트 제외 (Playwright 사용)
      '**/.{idea,git,cache,output,temp}/**',
    ],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'text-summary'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/__tests__/**',
        'dist/',
        'src/main.tsx',
        'src/vite-env.d.ts',
      ],
    },
  },
})