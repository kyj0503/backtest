import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
const target = process.env.API_PROXY_TARGET || 'http://localhost:8001'
// When running inside Docker Compose, use service hostnames on the shared network.
const SPRING_TARGET = process.env.SPRING_PROXY_TARGET || 'http://backtest-be-spring:8080';
const FASTAPI_TARGET = process.env.FASTAPI_PROXY_TARGET || 'http://backtest_be_fast:8000';

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
    proxy: {
      // Spring Boot 서버 (인증, 사용자 관리, 채팅)
      '/api/auth': {
        target: SPRING_TARGET,
        changeOrigin: true,
        headers: {
          host: 'localhost',
        }
      },
      '/api/users': {
        target: SPRING_TARGET,
        changeOrigin: true,
        headers: {
          host: 'localhost',
        }
      },
      '/api/chat': {
        target: SPRING_TARGET,
        changeOrigin: true,
        headers: {
          host: 'localhost',
        }
      },
      // WebSocket (STOMP) 연결을 위한 프록시
      '/ws': {
        target: SPRING_TARGET,
        changeOrigin: true,
        ws: true, // WebSocket 지원 활성화
        headers: {
          host: 'localhost',
        }
      },
      // FastAPI 서버 (백테스트 - 인증 불필요)
      '/api/v1/backtest': {
        target: FASTAPI_TARGET,
        changeOrigin: true,
        headers: {
          host: 'localhost',
        }
      },
      // 기타 API 요청은 Spring Boot로 (기본값)
      '/api': {
        target: SPRING_TARGET,
        changeOrigin: true,
        headers: {
          host: 'localhost',
        }
      }
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