#!/usr/bin/env bash
# Python(develop) 기준 픽스처 입력을 backtest_be_go/testdata/python/ 으로 내보낸다.
#
# 1) backtest_be_fast 이미지를 --target test로 빌드한다. 빌드 중 develop의 unit/e2e
#    테스트(스냅샷, 골든 마스터 포함)가 통과해야 이미지가 만들어진다.
# 2) 그 이미지에서 네트워크 없이 export_inputs.py를 실행한다.
#
# Python 제거(go-migration 3.10) 이후에는 실행할 수 없다. 절차는 HISTORY.md에 남긴다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="backtest-python-reference:export"
OUT_DIR="$ROOT/backtest_be_go/testdata/python"
SOURCE_COMMIT="$(git -C "$ROOT" log -1 --format=%H -- backtest_be_fast)"

docker build --target test -t "$IMAGE" "$ROOT/backtest_be_fast"

mkdir -p "$OUT_DIR"
# MSYS_NO_PATHCONV: Git Bash(Windows)가 컨테이너 경로를 호스트 경로로 바꾸지 않게 한다.
MSYS_NO_PATHCONV=1 docker run --rm --network none \
  -e SOURCE_COMMIT="$SOURCE_COMMIT" \
  -e EXPORT_OUT=/out \
  -v "$ROOT/scripts/python-reference:/export:ro" \
  -v "$OUT_DIR:/out" \
  -w /app \
  "$IMAGE" python -I /export/export_inputs.py

# 3) 내보낸 입력만으로 Python 응답이 스냅샷과 같게 재현되는지 확인한다 (읽기 전용 마운트).
MSYS_NO_PATHCONV=1 docker run --rm --network none \
  -v "$ROOT/scripts/python-reference:/export:ro" \
  -v "$OUT_DIR:/out:ro" \
  -w /app \
  "$IMAGE" python -I /export/verify_inputs.py

# 4) FastAPI가 생성한 OpenAPI 문서를 Go 서버의 정적 openapi.json 초기본으로 내보낸다.
#    이후 Go 쪽에서 의도적으로 바뀌는 계약은 backtest_be_go/internal/api/openapi.json을 직접 고친다.
MSYS_NO_PATHCONV=1 docker run --rm --network none -w /app "$IMAGE" \
  python -I -c "import sys, json; sys.path.insert(0, '/app'); from app.main import app; print(json.dumps(app.openapi(), ensure_ascii=False, indent=1))" \
  | grep -v '^네이버' > "$OUT_DIR/contract/openapi.json"
