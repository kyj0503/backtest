#!/usr/bin/env bash
# compose.bench.yaml의 세 API를 새 프로세스로 다시 띄우고(컨테이너는 남긴다) 32개 시나리오를 확인한 뒤,
# 시나리오당 순차 10회와 동시 2·8·16건을 측정한다. 관측기는 별도 cgroup에서 대상 컨테이너의 메모리를 읽는다.
#
# 결과: ${BENCH_RESULTS:-.comparison/bench-results/<시각>}/{python,rust,go}.json 과 요약 표.
# 모든 단계는 Docker로 실행한다.
set -euo pipefail
export MSYS_NO_PATHCONV=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && (pwd -W 2>/dev/null || pwd))"
INPUTS="${BENCH_INPUTS:-$ROOT/.comparison/bench-3way/inputs}"
OUT="${BENCH_RESULTS:-$ROOT/.comparison/bench-results/$(date +%Y%m%d-%H%M%S)}"
NET=backtest-bench_default
[ -f "$INPUTS/prices.json" ] || { echo "benchmark inputs not found: $INPUTS" >&2; exit 2; }
mkdir -p "$OUT"

docker compose -f "$ROOT/compose.bench.yaml" up -d --build
docker run --rm --network "$NET" -v "$ROOT/scripts/benchmark:/scripts:ro" -v "$INPUTS:/inputs:ro" \
  python:3.13-slim python /scripts/check.py
docker compose -f "$ROOT/compose.bench.yaml" up -d --force-recreate bench-python-api bench-rust-api bench-go-api
for impl in python rust go; do
  docker run --rm --network "$NET" --pid "container:backtest-bench-$impl-api" --cgroupns host \
    -v "$ROOT/scripts/benchmark:/scripts:ro" -v "$INPUTS:/inputs:ro" -v "$OUT:/reports" \
    python:3.13-slim python /scripts/benchmark-memory.py --server "$impl" --samples-root /inputs \
    --output /reports --readiness-path /health --repeats 10 > "$OUT/$impl.log"
  echo "$impl done"
done
docker run --rm --network none -v "$ROOT/scripts/benchmark:/scripts:ro" -v "$OUT:/reports:ro" \
  python:3.13-slim python /scripts/summarize.py | tee "$OUT/summary.txt"
echo "results: $OUT"
