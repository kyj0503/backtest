import { defineConfig, mergeConfig } from 'vite';
import baseConfig from './vite.config';

// Mounted beside each console's original config. Only local server routing is
// overlaid: the legacy console also needs the four independent reference APIs.
export default defineConfig(env => mergeConfig(baseConfig(env), {
  server: {
    hmr: false,
    proxy: {
      '/api/v1': {
        target: process.env.BACKTEST_PROXY_TARGET,
        changeOrigin: true,
        proxyTimeout: 180_000,
      },
    },
  },
}));
