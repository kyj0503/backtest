#!/usr/bin/env bash
set -euo pipefail

echo "[verify] Building and testing backend (Docker build with tests) ..."
docker build \
  --build-arg RUN_TESTS=true \
  --build-arg PYTEST_ADDOPTS="-m 'not integration and not e2e'" \
  -t backtest-backend-test:verify ./backend

echo "[verify] Building and testing frontend (Docker build with tests) ..."
docker build \
  --build-arg RUN_TESTS=true \
  -t backtest-frontend-test:verify ./frontend

echo "[verify] Running backend container and checking health ..."
cid=$(docker run -d -p 8001:8000 --rm backtest-backend-test:verify)
cleanup() { docker stop "$cid" >/dev/null 2>&1 || true; }
trap cleanup EXIT

# Wait for server
for i in {1..30}; do
  if curl -fsS http://localhost:8001/health >/dev/null 2>&1; then
    echo "[verify] Backend health OK"; break; fi
  sleep 1
  if [ "$i" -eq 30 ]; then
    echo "[verify] Backend did not become healthy in time" >&2
    exit 1
  fi
done

echo "[verify] All checks passed"
