#!/usr/bin/env bash
# 운영 DB 덤프를 로컬 검증용 DB(compose.devdb.yaml)에 적재하고 goose 전환을 리허설한다.
#
# 1) 덤프 만들기 — 로컬이 아니라 관리형 MySQL에 닿는 OCI 앱 서버(또는 배스천)에서 사람이 실행한다.
#    접속 정보는 그 서버의 환경에서 직접 넣는다. 가능하면 읽기 전용 계정을 쓴다:
#
#      mysqldump --single-transaction --set-gtid-purged=OFF --no-tablespaces \
#        -h <db-host> -u <user> -p --ssl-ca=/opt/backtest/production/tls/oracle-mysql-ca.pem \
#        stock_data_cache | gzip > stock_data_cache-$(date +%Y%m%d).sql.gz
#
# 2) 덤프 파일을 로컬로 가져와 저장소 밖 또는 .local-db/(gitignore)에 둔다. 커밋하지 않는다.
# 3) 이 스크립트를 실행한다:  scripts/load-devdb.sh .local-db/stock_data_cache-YYYYMMDD.sql.gz
#
# 하는 일:
#   - devdb 컨테이너를 띄우고, 비어 있는 DB에만 덤프를 적재한다(이미 테이블이 있으면 멈춘다).
#   - 다시 적재하려면 devdb의 stock_data_cache를 비운 뒤(DROP/CREATE DATABASE) 같은 덤프로 다시 실행한다.
#     덤프 파일이 원본이므로 따로 스냅샷을 만들지 않는다.
#   - backtestctl migrate detect → baseline <감지 버전> → up으로 운영 전환 절차를 그대로 리허설한다.
#
# 모든 단계는 Docker로 실행한다. 원격 DB에는 접속하지 않는다.
set -euo pipefail
export MSYS_NO_PATHCONV=1

DUMP="${1:?usage: $0 <dump.sql.gz>}"
# Git Bash(Windows)에서는 pwd -W가 C:/... 경로를 준다. MSYS_NO_PATHCONV와 함께 써도 docker가 해석할 수 있다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && (pwd -W 2>/dev/null || pwd))"
ROOT_PW="${DEVDB_ROOT_PASSWORD:-devdb-root-local}"
[ -f "$DUMP" ] || { echo "dump not found: $DUMP" >&2; exit 2; }
docker network inspect backtest-network >/dev/null 2>&1 || {
  echo "network backtest-network is missing: run 'docker compose -f compose.dev.yaml up -d mysql' first" >&2
  exit 2
}

docker compose -f "$ROOT/compose.devdb.yaml" up -d devdb
q() { docker exec -e MYSQL_PWD="$ROOT_PW" backtest-devdb mysql -uroot -N --default-character-set=utf8mb4 stock_data_cache "$@"; }
# 초기화 단계의 임시 서버는 소켓으로만 뜨고 헬스체크(ping)도 통과한다. TCP 접속이 되어야 초기화가 끝난 것이다.
for _ in $(seq 180); do
  if docker exec -e MYSQL_PWD="$ROOT_PW" backtest-devdb mysql -uroot -h127.0.0.1 --protocol=TCP -e 'SELECT 1' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

tables="$(q -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='stock_data_cache'")"
if [ "$tables" != "0" ]; then
  echo "stock_data_cache already has $tables tables; refusing to overwrite. Drop the database first to reload." >&2
  exit 1
fi

echo "loading $DUMP ..."
gzip -dc "$DUMP" | docker exec -i -e MYSQL_PWD="$ROOT_PW" backtest-devdb \
  mysql -uroot --default-character-set=utf8mb4 stock_data_cache
q -e "SELECT 'stocks', COUNT(*) FROM stocks UNION ALL SELECT 'daily_prices', COUNT(*) FROM daily_prices UNION ALL SELECT 'stock_news', COUNT(*) FROM stock_news"

docker build -q -t backtest-be-go:runtime "$ROOT/backtest_be_go" >/dev/null
ctl() {
  docker run --rm --network backtest-network --entrypoint /app/backtestctl \
    -e DATABASE_URL="mysql://root:$ROOT_PW@backtest-devdb:3306/stock_data_cache?charset=utf8mb4" \
    backtest-be-go:runtime "$@"
}
version="$(ctl migrate detect)"
echo "detected schema version: $version"
ctl migrate baseline "$version"
ctl migrate up
ctl migrate status
ctl check-orphans || echo "orphan rows found (check-orphans exit code 1); review before deleting"
echo "done. Point the Go server at it with DATABASE_URL=mysql://root:...@backtest-devdb:3306/stock_data_cache"
