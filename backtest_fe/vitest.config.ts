/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import path from 'path'

// Determine reporters dynamically for CI environments
const isCI = process.env.CI === '1' || process.env.CI === 'true'
// Allow overriding JUnit output path from environment (e.g., Jenkins step)
const junitOutputFile = process.env.VITEST_JUNIT_FILE || 'reports/frontend/junit.xml'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    css: true,
    reporters: isCI ? [
      'default',
      ['junit', { outputFile: junitOutputFile }]
    ] : ['default'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.js',
        '**/*.config.ts',
      ]
    }
  },
})
