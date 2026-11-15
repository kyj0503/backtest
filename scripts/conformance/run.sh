#!/usr/bin/env bash
# 세 백엔드를 고정 시세로 빌드·기동하고 Go 기준 적합성 검사를 돌린다(Docker 전용). 컨테이너는 남긴다.
#   bash scripts/conformance/run.sh [python,rust]
# 여러 작업이 동시에 돌 때는 CONFORMANCE_PROJECT로 compose 프로젝트(네트워크·컨테이너)를 나눈다.
set -euo pipefail
export MSYS_NO_PATHCONV=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
PROJECT="${CONFORMANCE_PROJECT:-backtest-conformance}"
OUT="${CONFORMANCE_RESULTS:-$ROOT/.comparison/$PROJECT}"
TARGETS="${1:-python,rust}"
mkdir -p "$OUT"
docker compose -p "$PROJECT" -f "$ROOT/compose.conformance.yaml" up -d --build --force-recreate
docker run --rm --network "${PROJECT}_default" \
  -v "$ROOT/scripts/conformance:/scripts:ro" -v "$ROOT/backtest_be_go/testdata/rust:/cases:ro" -v "$OUT:/reports" \
  python:3.13-slim sh -c "python /scripts/wait.py && python /scripts/conformance.py --out /reports --only $TARGETS"
echo "report: $OUT/conformance.json"
