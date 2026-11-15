#!/usr/bin/env bash
# Go 백엔드의 MySQL 통합 테스트(go test -tags integration)를 Docker로 실행한다.
#
# 임시 네트워크에 tmpfs MySQL을 띄우고, backtest_be_go의 test 스테이지 이미지 안에서 테스트를 돌린다.
# 호스트 포트와 바인드 마운트를 쓰지 않는다. 임시 리소스는 성공·실패와 무관하게 정리한다.
#
# 환경변수(선택): MYSQL_IMAGE (기본: compose.dev.yaml과 같은 이미지), DOCKER (기본: docker)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER="${DOCKER:-docker}"
MYSQL_IMAGE="${MYSQL_IMAGE:-mysql:innovation@sha256:f51c9c01c16b0eb5d81bb70ab7e7fcb3b96abc6a54114be3a94e8e569cae7815}"
PREFIX="go-integration-$$"
NET="$PREFIX-net"
DB="$PREFIX-mysql"
IMAGE="backtest-be-go:test"
ROOT_PW="integration-root-pw"

cleanup() {
  "$DOCKER" rm -f "$DB" >/dev/null 2>&1 || true
  "$DOCKER" network rm "$NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT

"$DOCKER" build -q --target test -t "$IMAGE" "$ROOT/backtest_be_go" >/dev/null
"$DOCKER" network create "$NET" >/dev/null
MSYS_NO_PATHCONV=1 "$DOCKER" run -d --name "$DB" --network "$NET" --tmpfs /var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD="$ROOT_PW" "$MYSQL_IMAGE" >/dev/null

for _ in $(seq 120); do
  if "$DOCKER" exec -e MYSQL_PWD="$ROOT_PW" "$DB" mysql -uroot -h127.0.0.1 --protocol=TCP -e 'SELECT 1' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

"$DOCKER" run --rm --network "$NET" \
  -e TEST_MYSQL_ROOT_DSN="root:$ROOT_PW@tcp($DB:3306)/" \
  -e GOFLAGS=-mod=readonly \
  "$IMAGE" go test -tags integration -count=1 -race ./...
