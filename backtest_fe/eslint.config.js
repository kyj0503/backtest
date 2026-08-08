// ESLint flat config (ESLint 10).
//
// Migrated from the legacy `eslintConfig` block that used to live in
// package.json:
//
//   "eslintConfig": {
//     "extends": [
//       "plugin:@typescript-eslint/recommended",
//       "plugin:react-hooks/recommended"
//     ]
//   }
//
// This file is intentionally RULE-EQUIVALENT to that setup: the same 26 rules
// are active on the same set of files (**/*.ts, **/*.tsx). See the react-hooks
// note below for the one place where an explicit rule list replaces a preset.

import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import reactHooks from 'eslint-plugin-react-hooks'

export default [
  // Build output, coverage and tooling artifacts. Under eslintrc these were
  // never linted in practice because `--ext ts,tsx` matched nothing inside
  // them; flat config has no `--ext`, so they must be ignored explicitly.
  {
    ignores: [
      'dist/**',
      'build/**',
      'coverage/**',
      'node_modules/**',
      'playwright-report/**',
      'test-results/**',
      '.vite/**',
    ],
  },

  // `plugin:@typescript-eslint/recommended` -> flat equivalent.
  // Scoped to ts/tsx so the TypeScript parser is not applied to plain .js
  // config files (postcss.config.js, tailwind.config.js, this file).
  ...tseslint.configs['flat/recommended'].map((config) => ({
    ...config,
    files: ['**/*.ts', '**/*.tsx'],
  })),

  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsparser,
      ecmaVersion: 'latest',
      sourceType: 'module',
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    linterOptions: {
      reportUnusedDisableDirectives: 'error',
    },
    plugins: {
      'react-hooks': reactHooks,
    },
    rules: {
      // eslint-plugin-react-hooks v7 no longer ships a `recommended` preset
      // that is equivalent to v4's: v7's presets additionally enable ~27
      // React Compiler rules. To stay rule-equivalent with the previous
      // `plugin:react-hooks/recommended` (v4), the two original rules are
      // listed explicitly at their original severities.
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
]
