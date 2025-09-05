import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
const target = process.env.API_PROXY_TARGET || 'http://localhost:8001'

export default defineConfig({
  plugins: [react()],
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0'),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target,
        changeOrigin: true,
      }
    }
  }
})