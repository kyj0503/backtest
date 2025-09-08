# Contributing Guide

## Pre-commit verification (mandatory)

All commits must pass build, tests, and a lightweight runtime health check.

- Configure Git hooks once:
  ```bash
  git config core.hooksPath .githooks
  ```
- Commit flow:
  ```bash
  # develop changes
  git add -A
  git commit -m "type(scope): message"
  # pre-commit hook runs scripts/verify-before-commit.sh automatically
  ```

If you want to run the verification manually:
```bash
scripts/verify-before-commit.sh
```
This script builds and tests backend/frontend (Docker) and verifies `/health`.

## Backend dependencies (uv)

- We use [uv](https://github.com/astral-sh/uv) instead of pip for fast installs.
- Docker builds install Python deps via `uv pip install --system -r requirements.txt`.
- Local (optional): `uv pip install --system -r requirements.txt`.

## Commit messages

Follow `COMMIT_CONVENTION.md` (Conventional Commits, scoped for monorepo).

## CI

Jenkins builds images and runs tests; local verification mirrors CI steps to minimize surprises.
