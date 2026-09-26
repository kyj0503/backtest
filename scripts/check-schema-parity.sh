#!/usr/bin/env sh
# schema.sql(initdb) 경로와 Alembic `upgrade head` 경로의 최종 스키마 정합성 검사 (A-11)
#
# 빈 MySQL 컨테이너 두 개를 띄워 한쪽은 database/schema.sql을 initdb로, 다른
# 쪽은 backtest_be_fast/alembic의 `upgrade head`로 스키마를 만든 뒤, 세 테이블의
# SHOW CREATE TABLE(컬럼·테이블 COMMENT 포함)과 테이블 목록, DB 기본 charset을
# 비교한다. 하나라도 다르면 diff를 출력하고 종료 코드 1. 임시 컨테이너와
# 네트워크는 성공·실패와 무관하게 정리한다.
#
# 스키마를 바꿀 때는 schema.sql과 새 Alembic 리비전을 함께 고치고 이 스크립트로
# 두 경로가 같은 결과를 내는지 확인한다. autogenerate용 ORM 메타데이터가 없어
# (alembic/env.py 참고) 이 비교가 두 정의를 묶는 유일한 장치다.
#
# 구현 메모: 바인드 마운트(-v)와 호스트 포트를 쓰지 않는다. schema.sql은
# `docker cp -`(tar 스트림)로 initdb 디렉터리에 넣고, Alembic은 같은 임시
# 네트워크의 python 컨테이너 안에서 실행하며 소스를 표준 입력 tar로 넘긴다.
# 그래서 Jenkins처럼 컨테이너 안에서 호스트 데몬에 붙는 환경(scripts/audit-deps.sh
# 머리말 참고)이나 Windows docker.exe를 WSL에서 부르는 경우에도 경로 변환 없이
# 동작한다. Alembic 컨테이너는 requirements.lock.txt의 고정 버전을 pip로 설치하므로
# 인터넷 접근이 필요하다.
#
# 사용: scripts/check-schema-parity.sh
# 환경변수(모두 선택):
#   DOCKER         docker 명령 (기본: docker). 예: DOCKER=docker.exe
#   MYSQL_IMAGE    비교에 쓸 MySQL 이미지 (기본: mysql:8.4, compose와 동일)
#   PY_IMAGE       Alembic 실행 이미지 (기본: python:3.11-slim, BE Dockerfile과 동일)
#   SCHEMA_SQL     비교할 initdb 스크립트 (기본: database/schema.sql)
#   PARITY_PREFIX  임시 리소스 이름 접두사 (기본: schema-parity-<pid>)
#   KEEP_DUMPS     비어 있지 않으면 비교에 쓴 덤프 디렉터리를 지우지 않는다
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BE_DIR="$REPO_ROOT/backtest_be_fast"

DOCKER="${DOCKER:-docker}"
MYSQL_IMAGE="${MYSQL_IMAGE:-mysql:8.4}"
PY_IMAGE="${PY_IMAGE:-python:3.11-slim}"
SCHEMA_SQL="${SCHEMA_SQL:-$REPO_ROOT/database/schema.sql}"
PREFIX="${PARITY_PREFIX:-schema-parity-$$}"

DB_NAME="stock_data_cache"
ROOT_PW="parity-root-pw"
TABLES="stocks daily_prices stock_news"
READY_TIMEOUT=180

NET="$PREFIX-net"
C_INITDB="$PREFIX-initdb"
C_ALEMBIC="$PREFIX-alembic"
WORK="$(mktemp -d)"

cleanup() {
  "$DOCKER" rm -f "$C_INITDB" "$C_ALEMBIC" >/dev/null 2>&1 || true
  "$DOCKER" network rm "$NET" >/dev/null 2>&1 || true
  if [ -n "${KEEP_DUMPS:-}" ]; then
    echo "덤프 보존: $WORK"
  else
    rm -rf "$WORK"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT TERM

[ -f "$SCHEMA_SQL" ] || { echo "schema.sql 없음: $SCHEMA_SQL" >&2; exit 2; }

# Alembic 실행에 필요한 패키지를 BE 락 파일의 고정 버전으로 설치한다.
PIP_PKGS="$(grep -i -E '^(alembic|sqlalchemy|pymysql|cryptography|mako|markupsafe|greenlet|typing_extensions)==' \
  "$BE_DIR/requirements.lock.txt" | tr '\n' ' ')"
[ -n "$PIP_PKGS" ] || { echo "requirements.lock.txt에서 alembic 의존성을 찾지 못함" >&2; exit 2; }

mysql_exec() {
  # $1=컨테이너, 나머지=mysql 인자. 비밀번호는 명령줄 경고를 피하려 MYSQL_PWD로 넘긴다.
  _c="$1"; shift
  "$DOCKER" exec -e MYSQL_PWD="$ROOT_PW" "$_c" \
    mysql --default-character-set=utf8mb4 -uroot "$@"
}

wait_ready() {
  # initdb 단계의 임시 서버는 --skip-networking으로 뜨므로, TCP 접속이 되면
  # initdb가 끝나고 본 서버가 올라온 것이다.
  _c="$1"; _i=0
  while [ "$_i" -lt "$READY_TIMEOUT" ]; do
    _state="$("$DOCKER" inspect -f '{{.State.Running}}' "$_c" 2>/dev/null || echo false)"
    if [ "$_state" != "true" ]; then
      echo "컨테이너 $_c 가 중단됐다 (initdb 실패 가능성). 로그:" >&2
      "$DOCKER" logs --tail 40 "$_c" >&2 || true
      exit 2
    fi
    if mysql_exec "$_c" -h127.0.0.1 --protocol=TCP -e 'SELECT 1' >/dev/null 2>&1; then
      return 0
    fi
    sleep 1; _i=$((_i + 1))
  done
  echo "컨테이너 $_c 가 ${READY_TIMEOUT}초 안에 준비되지 않았다" >&2
  "$DOCKER" logs --tail 40 "$_c" >&2 || true
  exit 2
}

dump_schema() {
  # $1=컨테이너, $2=출력 파일. alembic_version은 Alembic 경로에만 있으므로 제외한다.
  _c="$1"; _out="$2"
  {
    echo "## SHOW CREATE DATABASE"
    mysql_exec "$_c" -N -B --raw -e "SHOW CREATE DATABASE \`$DB_NAME\`"
    echo "## TABLES"
    mysql_exec "$_c" -N -B --raw "$DB_NAME" -e "SHOW TABLES" | grep -v '^alembic_version$' | sort
    for _t in $TABLES; do
      echo "## SHOW CREATE TABLE $_t"
      mysql_exec "$_c" -N -B --raw "$DB_NAME" -e "SHOW CREATE TABLE \`$_t\`"
    done
  } | sed -E 's/ AUTO_INCREMENT=[0-9]+//' > "$_out"
}

echo "== 스키마 정합성 검사: $MYSQL_IMAGE, $(basename "$SCHEMA_SQL") vs alembic upgrade head =="

"$DOCKER" network create "$NET" >/dev/null

# 1) initdb 경로: compose와 같이 01-schema.sql로 initdb 디렉터리에 둔다.
mkdir "$WORK/initdb"
cp "$SCHEMA_SQL" "$WORK/initdb/01-schema.sql"
"$DOCKER" create --name "$C_INITDB" --network "$NET" \
  -e MYSQL_ROOT_PASSWORD="$ROOT_PW" -e MYSQL_DATABASE="$DB_NAME" \
  "$MYSQL_IMAGE" >/dev/null
tar -C "$WORK/initdb" -cf - 01-schema.sql | "$DOCKER" cp - "$C_INITDB:/docker-entrypoint-initdb.d/"
"$DOCKER" start "$C_INITDB" >/dev/null

# 2) Alembic 경로: initdb 없이 빈 DB만 만든다 (compose의 MYSQL_DATABASE와 같은 방식).
"$DOCKER" run -d --name "$C_ALEMBIC" --network "$NET" \
  -e MYSQL_ROOT_PASSWORD="$ROOT_PW" -e MYSQL_DATABASE="$DB_NAME" \
  "$MYSQL_IMAGE" >/dev/null

wait_ready "$C_INITDB"
wait_ready "$C_ALEMBIC"
echo "MySQL 두 개 준비 완료 ($("$DOCKER" exec "$C_INITDB" mysqld --version | sed 's/^.*Ver //'))"

# env.py는 app 패키지를 import하지 못하면 DATABASE_URL로 폴백한다(ImportError 처리).
# 여기서는 alembic.ini와 alembic/만 넘기므로 그 폴백 경로를 탄다.
tar -C "$BE_DIR" --exclude=__pycache__ -cf - alembic.ini alembic \
  | "$DOCKER" run --rm -i --network "$NET" \
      -e DATABASE_URL="mysql+pymysql://root:$ROOT_PW@$C_ALEMBIC:3306/$DB_NAME?charset=utf8mb4" \
      -e PIP_DISABLE_PIP_VERSION_CHECK=1 -e PIP_ROOT_USER_ACTION=ignore \
      "$PY_IMAGE" sh -c "mkdir /w && cd /w && tar xf - && pip install --quiet $PIP_PKGS && python -m alembic upgrade head && python -m alembic current"

dump_schema "$C_INITDB" "$WORK/initdb.txt"
dump_schema "$C_ALEMBIC" "$WORK/alembic.txt"

if diff -u --label "schema.sql (initdb)" --label "alembic upgrade head" \
     "$WORK/initdb.txt" "$WORK/alembic.txt"; then
  echo "OK: 두 경로의 스키마가 동일하다 ($(echo $TABLES | wc -w)개 테이블, COMMENT 포함)"
else
  echo "FAIL: schema.sql과 Alembic head의 스키마가 다르다 (위 diff 참고)" >&2
  exit 1
fi
