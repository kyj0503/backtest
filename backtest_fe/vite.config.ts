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
      '/api/v1/naver-news': {
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
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          // 차트 라이브러리 분리
          'chart-vendor': ['recharts'],
          // 아이콘 라이브러리 분리
          'icon-vendor': ['react-icons'],
          // 유틸리티 라이브러리 분리
          'util-vendor': ['axios']
        }
      }
    },
    // 청크 크기 경고 임계값 설정
    chunkSizeWarningLimit: 1000,
    // 소스맵 생성 (개발 시에만)
    sourcemap: mode === 'development'
  }
}))
