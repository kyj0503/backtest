#!/usr/bin/env bash
# compose.loadtest.yaml의 세 API를 한 번에 하나씩 같은 단계로 부하 측정한다(Docker 전용). 컨테이너는 남긴다.
#
#   bash scripts/loadtest/run.sh [go rust python]
#
# 구현마다: 새 프로세스로 다시 띄움 → 준비 확인 → 예열 20초 → POST 동시 사용자 단계 → GET 단계.
# 단계마다 docker stats로 CPU·메모리를 표본 추출한다. 결과: ${LOAD_RESULTS:-.comparison/load-results/<시각>}
set -euo pipefail
export MSYS_NO_PATHCONV=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
INPUTS="${BENCH_INPUTS:-$ROOT/.comparison/bench-3way/inputs}"
OUT="${LOAD_RESULTS:-$ROOT/.comparison/load-results/$(date +%Y%m%d-%H%M%S)}"
IMPLS="${*:-go rust python}"
POST_LEVELS="${POST_LEVELS:-1 2 4 8 16 32 64}"
GET_LEVELS="${GET_LEVELS:-1 4 16}"
DURATION="${DURATION:-30s}"
NET=backtest-load_default
K6=grafana/k6:1.0.0
[ -f "$INPUTS/prices.json" ] || { echo "inputs not found: $INPUTS" >&2; exit 2; }
mkdir -p "$OUT"

compose() { docker compose -f "$ROOT/compose.loadtest.yaml" "$@"; }
k6() { # impl mode vus duration out
  docker run --rm --network "$NET" -v "$ROOT/scripts/loadtest:/scripts:ro" -v "$INPUTS:/inputs:ro" -v "$OUT:/reports" \
    "$K6" run -q --no-color -e BASE="http://load-$1-api:8000" -e MODE="$2" -e VUS="$3" -e DURATION="$4" -e OUT="/reports/$5" \
    /scripts/load.js >/dev/null
}
sample() { # container file — 1초 남짓 간격으로 CPU%;메모리 사용량을 기록
  while :; do docker stats --no-stream --format '{{.CPUPerc}};{{.MemUsage}}' "$1" >> "$2" 2>/dev/null || true; done
}

compose up -d --build
for impl in $IMPLS; do
  c="backtest-load-$impl-api"
  compose up -d --force-recreate "load-$impl-api"
  docker run --rm --network "$NET" curlimages/curl:8.11.1 -sf --retry 120 --retry-delay 1 --retry-all-errors \
    -o /dev/null "http://load-$impl-api:8000/health/ready"
  docker stats --no-stream --format '{{.MemUsage}}' "$c" > "$OUT/$impl-idle.mem"
  k6 "$impl" post 4 20s "$impl-warmup.json"
  docker stats --no-stream --format '{{.MemUsage}}' "$c" > "$OUT/$impl-warm.mem"
  for mode in post get; do
    levels=$POST_LEVELS; [ "$mode" = get ] && levels=$GET_LEVELS
    for v in $levels; do
      sample "$c" "$OUT/$impl-$mode-$v.stats" & sp=$!
      k6 "$impl" "$mode" "$v" "$DURATION" "$impl-$mode-$v.json"
      kill "$sp" 2>/dev/null || true; wait "$sp" 2>/dev/null || true
      echo "$impl $mode vus=$v done"
      sleep 3
    done
  done
done
docker run --rm --network none -v "$ROOT/scripts/loadtest:/scripts:ro" -v "$OUT:/reports" \
  python:3.13-slim python /scripts/summarize.py /reports | tee "$OUT/summary.md"
echo "results: $OUT"
