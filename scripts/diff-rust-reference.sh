#!/usr/bin/env bash
# Go 엔진과 Rust 구현(backtest_be_rust)의 차등 비교(보조 검증, Docker 전용).
#
# 1) 저장소의 backtest_be_rust로 Rust 런타임 이미지를 빌드한다.
# 2) 고정 시세(testdata/rust/histories.json)로 rust 서버를 띄우고 parity.json 64개 요청의 응답을 모은다.
# 3) Go 테스트(-tags diff)가 같은 입력으로 엔진을 돌려 필드별로 비교한다(상대 오차 1e-9).
#
# 합격 기준은 Go의 불변식 테스트다. 이 비교는 독립 구현 두 개가 같은 계약에 도달했는지 보는 용도다.
# 결과 파일은 저장소에 넣지 않는다.
set -euo pipefail
export MSYS_NO_PATHCONV=1

# Git Bash(Windows)에서는 pwd -W가 C:/... 경로를 준다. MSYS_NO_PATHCONV와 함께 써도 docker가 해석할 수 있다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && (pwd -W 2>/dev/null || pwd))"
WORK="$(cd "$(mktemp -d)" && (pwd -W 2>/dev/null || pwd))"
NET="rust-diff-$$"
IMAGE="backtest-rust-ref:local"
cleanup() {
  docker rm -f "$NET-rust" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  rm -rf "$WORK"
}
trap cleanup EXIT

mkdir -p "$WORK/w"
docker build -q --target runtime -t "$IMAGE" "$ROOT/backtest_be_rust" >/dev/null
cp "$ROOT/backtest_be_go/testdata/rust/histories.json" "$ROOT/backtest_be_go/testdata/rust/parity.json" "$WORK/w/"
cat > "$WORK/w/collect.py" <<'EOF'
import json, sys, urllib.request, time
base = sys.argv[1]
for _ in range(50):
    try:
        urllib.request.urlopen(base + '/health', timeout=1); break
    except Exception:
        time.sleep(0.2)
out = {}
for c in json.load(open('/w/parity.json')):
    req = dict(c['request'])
    for k in ['include_stock_data', 'include_volatility_events', 'include_exchange_rates', 'include_benchmarks', 'include_news']:
        req[k] = False
    r = urllib.request.Request(base + '/api/v1/backtest', data=json.dumps(req).encode(), headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            out[c['name']] = {'status': resp.status, 'body': json.load(resp)}
    except urllib.error.HTTPError as e:
        out[c['name']] = {'status': e.code, 'body': json.load(e)}
json.dump(out, open('/w/rust-out.json', 'w'), ensure_ascii=False)
print('collected', len(out), 'rust responses')
EOF

docker network create "$NET" >/dev/null
docker run -d --name "$NET-rust" --network "$NET" -e DEBUG=true -e TURNSTILE_ENABLED=false \
  -e BACKTEST_FIXTURE_FILE=/w/histories.json -v "$WORK/w:/w:ro" "$IMAGE" >/dev/null
docker run --rm --network "$NET" -v "$WORK/w:/w" python:3.13-slim python -I /w/collect.py "http://$NET-rust:8000"

docker build -q --target test -t backtest-be-go:test "$ROOT/backtest_be_go" >/dev/null
docker run --rm -v "$WORK/w:/w:ro" -e DIFF_RUST_OUT=/w/rust-out.json backtest-be-go:test \
  go test -tags diff -count=1 -run RustDiff ./internal/engine
