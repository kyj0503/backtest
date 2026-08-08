import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
// When running inside Docker Compose, use service hostnames on the shared network.
const FASTAPI_TARGET = process.env.FASTAPI_PROXY_TARGET || 'http://localhost:8000';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    // Allow disabling HMR in environments where WebSocket connections fail
    // (e.g., AdGuard / corporate proxy / unfinished chat feature)
    hmr: process.env.DISABLE_HMR ? false : {
      host: 'localhost',
      protocol: 'ws',
      port: 5173,
    },
    // 캐시 무효화 및 개발 서버 안정성 개선
    watch: {
      usePolling: true,
      interval: 100,
    },
    // CORS 설정
    cors: true,
    proxy: {
      // FastAPI 서버 (백테스트 - 인증 불필요) - 먼저 매칭되어야 함
      '/api/v1/backtest': {
        target: FASTAPI_TARGET,
        changeOrigin: true,
      },
    }
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // React 관련 라이브러리 분리
          // React 19에서는 진입점이 react-dom/client 이므로 명시하지 않으면
          // react-dom 본체가 vendor 청크에 잡히지 않고 index로 흘러들어간다.
          'react-vendor': ['react', 'react-dom', 'react-dom/client', 'react-router-dom'],
          // 아이콘 라이브러리 분리
          'icon-vendor': ['lucide-react'],
          // 유틸리티 라이브러리 분리
          'util-vendor': ['axios']
          // P3-23: 'chart-vendor': ['recharts']를 의도적으로 제거했다 (실측:
          // b5-F-report.md). recharts는 lazy(() => import(...))로 감싼 차트
          // 컴포넌트에서만 쓰이는데도(App.tsx의 HomePage/PortfolioPage 라우트
          // 분할과 별개로), manualChunks로 강제 분리하면 Vite가 그 청크를
          // "공유 vendor"로 취급해 index.html에 <link rel="modulepreload">를
          // 무조건 넣었다 - 실제 브라우저 네트워크 요청으로 확인한 결과 차트를
          // 전혀 렌더링하지 않는 HomePage(`/`)에서도 427KB(gzip 122KB)
          // chart-vendor 청크가 매번 받아졌다. manualChunks 항목을 없애자
          // recharts는 그것을 실제로 쓰는 PortfolioPage 청크 안으로 자연스럽게
          // 흡수됐고, `/`에서는 더 이상 전혀 요청되지 않는다(재측정으로 확인).
          // 다시 추가하기 전에 같은 방식(실제 브라우저로 초기 로드 네트워크
          // 요청 측정)으로 재검증할 것 - "vendor 청크로 분리 = 초기 로드에서
          // 빠진다"는 보장이 아니다.
        }
      }
    },
    // 청크 크기 경고 임계값 설정
    chunkSizeWarningLimit: 1000,
    // 소스맵 생성 (개발 시에만)
    sourcemap: mode === 'development'
  }
}))
