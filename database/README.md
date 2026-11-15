# database — 스키마와 MySQL 운영 가이드

캐시 DB(`stock_data_cache`)의 스키마 정의 두 경로, Python(Alembic) 시절 DB를 goose로 넘기는 절차,
MySQL 8.0 데이터 볼륨을 8.4로 올린 실측 기록을 적는다.

## 스키마 정의는 두 곳에 있다

| 경로 | 언제 쓰나 | 파일 |
|---|---|---|
| initdb | 빈 데이터 디렉터리로 MySQL 컨테이너를 **처음** 띄울 때 공식 이미지가 1회 실행 | `database/schema.sql` (compose가 `/docker-entrypoint-initdb.d/01-schema.sql`로 마운트) |
| goose | 이미 떠 있는 DB에 이후 변경을 적용 | `backtest_be_go/migrations/NNNNN_*.sql` (서버·backtestctl 바이너리에 내장) |

ORM 메타데이터가 없으므로 두 정의는 사람이 맞춘다. 스키마를 바꿀 때는 **schema.sql과 새 goose 파일을
함께** 고치고 아래 검사로 확인한다. 이미 배포된 마이그레이션 파일은 고치지 않는다(적용된 DB와 이력이
어긋난다). 자동 downgrade는 두지 않는다. 되돌리려면 적용 전 백업을 복원한다.

| 버전 | 파일 | 내용 |
|---|---|---|
| 1 | `00001_baseline.sql` | Python 시절 Alembic head(`1f574a9ba22e`)와 같은 스키마 |
| 2 | `00002_price_precision.sql` | 가격 컬럼 `DECIMAL(19,4)` → `DECIMAL(38,18)` (rust-migration F14, Alembic `6f903c2a711b`와 같은 변경) |

### 정합성 검사: `scripts/check-schema-parity.sh`

```bash
scripts/check-schema-parity.sh                      # 기본: docker, compose와 같은 MySQL 이미지
DOCKER=docker.exe scripts/check-schema-parity.sh    # WSL에서 Windows Docker CLI 사용
```

빈 MySQL 두 개에 각각 schema.sql initdb와 `backtestctl migrate up`을 적용하고, DB 기본 charset·테이블
목록·세 테이블의 `SHOW CREATE TABLE`(컬럼·테이블 COMMENT 포함)을 비교한다. 다르면 diff를 출력하고 종료
코드 1, 같으면 0. 버전 테이블(`goose_db_version`, 과거 `alembic_version`)은 비교에서 뺀다. 임시
컨테이너·네트워크는 항상 정리한다. 바인드 마운트와 호스트 포트를 쓰지 않으므로 Jenkins(컨테이너 안에서
호스트 데몬 사용)에서도 그대로 돈다. 백엔드 런타임 이미지를 빌드하므로 인터넷이 필요하다.

주의할 점:

- **컬럼 설명은 `--` 주석이 아니라 `COMMENT` 절로** 쓴다. 마이그레이션이 같은 문구를 COMMENT로 만든다.
- **schema.sql 맨 위의 `SET NAMES utf8mb4;`를 지우지 말 것.** 공식 mysql 이미지의 initdb는 POSIX
  로케일의 mysql 클라이언트로 스크립트를 실행하며, 그 연결 문자셋은 `latin1`이다(실측:
  `character_set_client=latin1`). 이 줄이 없으면 한글 COMMENT가 이중 인코딩돼 `'주식'`이 `'ì£¼ì‹'`로
  저장된다. goose 경로는 Go 드라이버가 utf8mb4로 접속하므로 문제가 없다(통합 테스트가 확인한다).

### 기존 DB를 goose로 넘기기

goose 기록(`goose_db_version`)이 없는 DB에 `migrate up`을 실행하면 거부된다. 00001을 다시 실행하면
테이블이 이미 있어 실패하거나, 운이 나쁘면 빈 테이블을 만들 수 있기 때문이다. 먼저 실제 스키마 버전을
판별해 기록한다. `baseline`은 SQL을 실행하지 않고 판별 결과와 다른 버전이면 기록하지 않는다.

```bash
# 컨테이너 안에서 실행한다(서버와 같은 DATABASE_* / DATABASE_URL 환경 변수를 읽는다).
backtestctl migrate detect            # 1: DECIMAL(19,4) Python/Alembic head, 2: DECIMAL(38,18)
backtestctl migrate baseline <버전>   # 판별 결과와 같아야 한다. 반드시 백업 후
backtestctl migrate up                # 남은 버전 적용 (Python DB면 00002)
backtestctl migrate status
```

| DB가 만들어진 방식 | 절차 |
|---|---|
| 운영 DB(Python/Alembic `1f574a9ba22e`) | 백업 → `baseline 1` → `up` |
| rust-migration 브랜치에서 Alembic `6f903c2a711b`까지 올린 DB | `baseline 2` |
| 현재 schema.sql로 initdb한 DB | `baseline 2` (`detect`가 2를 돌려준다) |
| 빈 DB | `up` |
| 이미 goose로 관리 중 | `up` |
| 물리 FK 제거(A-10) **이전** schema.sql로 만든 DB | `detect`는 1을 돌려주지만 FK가 남아 있다. 먼저 git 이력의 Alembic `7b2e9c4f1a30`과 같은 FK 제거를 수동으로 적용한 뒤 `baseline 1` |

운영 이미지와 CI는 마이그레이션을 실행하지 않는다. 운영 서버에서는
`docker exec backtest-be /app/backtestctl migrate status`처럼 실행한다. 00002는 `daily_prices` 전체를 다시
쓰는 ALTER이므로 행 수에 비례해 시간이 걸린다. 로컬 복사본(`scripts/load-devdb.sh`)으로 먼저 리허설한다.
`alembic_version` 테이블은 지우지 않고 남겨 둔다(정리는 TODO).

### 운영 DB의 로컬 복사본: `compose.devdb.yaml` + `scripts/load-devdb.sh`

운영 DB 덤프를 로컬 검증용 DB에 올려 전환 절차와 실제 데이터 계산을 확인한다. 덤프는 관리형 MySQL에
닿는 OCI 서버에서 사람이 만든다(스크립트 머리말의 `mysqldump` 명령). 로컬에서는 원격 DB에 접속하지
않는다. 덤프 파일은 `.local-db/`(gitignore) 또는 저장소 밖에 둔다.

```bash
docker compose -f compose.dev.yaml up -d mysql      # 공유 네트워크(backtest-network) 준비
bash scripts/load-devdb.sh .local-db/stock_data_cache-YYYYMMDD.sql.gz
```

빈 DB에만 적재하고(테이블이 있으면 멈춘다) `detect → baseline → up → check-orphans`까지 실행한다.
복사본은 `127.0.0.1:3307`, 같은 네트워크에서는 `backtest-devdb:3306`이다. 볼륨(`backtest-devdb`)은 지우지
않는다.

### 기존 DB의 COMMENT는 저장소 정의와 다를 수 있다

2026-09-27 이전 schema.sql로 initdb한 DB(dev 볼륨, 운영 DB)는 COMMENT가 저장소 정의와 다르다.
동작에는 영향이 없다(`migrate detect`도 COMMENT가 아니라 컬럼 정밀도로 판별한다).

- 테이블 COMMENT 3개와 COMMENT가 있던 컬럼 5개가 위의 이중 인코딩 상태다
- 나머지 컬럼은 COMMENT가 없다(당시 schema.sql은 `--` 주석만 썼다)

맞추려면 각 컬럼 정의를 그대로 다시 적는 `MODIFY COLUMN`이 필요해, 운영 DB의 `SHOW CREATE TABLE`을 먼저
떠서 저장소 정의와 비교한 뒤에 진행한다(자동 마이그레이션으로 넣지 않았다, TODO A-32).

## MySQL 8.0 → 8.4 업그레이드

compose는 `mysql:8.4`를 쓰지만(P2-24), 8.0 시절에 만든 데이터 볼륨이 남아 있을 수 있다.
그 볼륨으로 8.4를 띄우면 서버가 데이터 디렉터리를 **자동으로 제자리 업그레이드**한다.

### 공식 지원 범위 (MySQL 8.4 Reference Manual)

- 8.0 → 8.4 LTS는 제자리 업그레이드, 논리 덤프·로드, 복제를 모두 지원한다. 공식 예시는
  `8.0.37 to 8.4.x LTS`다. 8.0이 그보다 오래됐다면 먼저 최신 8.0.x로 올린 뒤 8.4로 가는 것이
  안전하다(실측은 8.0.46 → 8.4.11만 했다).
  — https://dev.mysql.com/doc/refman/8.4/en/upgrade-paths.html
- **8.4 → 8.0 제자리 다운그레이드는 지원하지 않는다.** 되돌리려면 업그레이드 전에 떠 둔
  논리 덤프로 복원해야 한다.
  — https://dev.mysql.com/doc/refman/8.4/en/downgrading.html
- 8.0을 `innodb_fast_shutdown=2`로 운영했다면 종료 전에 1(기본값) 또는 0으로 바꾼다.
  — https://dev.mysql.com/doc/refman/8.4/en/upgrade-binary-package.html
- `mysql_native_password`는 8.4에서 **기본 비활성**이다(9.0에서 제거).
  — https://dev.mysql.com/doc/refman/8.4/en/native-pluggable-authentication.html

### 절차

1. 백업: `mysqldump --single-transaction --routines --events --default-character-set=utf8mb4
   -uroot -p stock_data_cache > backup.sql` (다운그레이드 경로가 없으므로 필수)
2. 인증 플러그인 확인: `SELECT user, host, plugin FROM mysql.user;` —
   `mysql_native_password` 계정이 있으면 아래 "인증" 절 참고
3. 8.0을 정상 종료: `docker stop -t 120 <컨테이너>` (SIGTERM → `Shutdown complete`, 종료 코드 0.
   기본 10초 대기로는 큰 버퍼 풀에서 강제 종료될 수 있다)
4. 같은 볼륨으로 `mysql:8.4` 기동. 로그에서 업그레이드 완료를 확인한다
5. 테이블·행 수·제약 확인 후, 스키마가 A-10 이전 상태라면 위 "기존 DB를 goose로 넘기기" 절차 적용

### 실측 결과 (mysql:8.0.46 → mysql:8.4.11, 2026-09-27)

A-10 이전 schema.sql(`git show e2d49d6^:database/schema.sql`, 물리 FK 있음)로 8.0 볼륨을
initdb하고 샘플 데이터(stocks 2 / daily_prices 20 / stock_news 2, 한글 포함)를 넣은 뒤
정상 종료하고, 같은 볼륨으로 8.4를 띄웠다.

업그레이드 로그(약 7초, 기동 명령 후 준비 완료까지 9초):

```
[MY-011090] Data dictionary upgrading from version '80023' to '80300'.
[MY-013413] Data dictionary upgrade from version '80023' to '80300' completed.
[MY-013381] Server upgrade from '80046' to '80411' started.
[MY-013381] Server upgrade from '80046' to '80411' completed.
[MY-010931] /usr/sbin/mysqld: ready for connections. Version: '8.4.11' ...
```

데이터 디렉터리에 `mysql_upgrade_history`(`{"version":"8.4.11","maturity":"LTS"}`)가 생기고,
두 번째 기동부터는 업그레이드 로그가 나오지 않는다.

- 보존: 행 수·한글 데이터·합계값, PK/UNIQUE/CHECK, 물리 FK(`daily_prices_ibfk_1`, CASCADE)
  모두 8.0과 동일. `CHECK TABLE` 3개 OK
- (당시 Python) Alembic: `stamp d5c3763b29e6` → `upgrade head`로 `7b2e9c4f1a30`(FK 제거)와 `1f574a9ba22e`가
  적용되어 FK 0개, CHECK 유지, 행 수 불변
- 롤백 시도: 업그레이드된 볼륨으로 8.0.46을 띄우면 기동 실패(종료 코드 1)
  `Invalid MySQL server downgrade: Cannot downgrade from 80411 to 80046. Downgrade is only
  permitted between patch releases.` — 백업 없이는 되돌릴 수 없다

### 인증: `mysql_native_password`

| 계정 | 8.0 플러그인 | 8.4 기본 설정 | 8.4 + `--mysql-native-password=ON` |
|---|---|---|---|
| `appuser`(이미지 엔트리포인트가 생성) | `caching_sha2_password` | 로그인 성공 | 성공 |
| `mysql_native_password`로 만든 계정 | `mysql_native_password` | **실패** `(1524, "Plugin 'mysql_native_password' is not loaded")` | 성공 |

- 공식 이미지가 `MYSQL_USER`로 만든 `appuser`는 8.0에서도 기본 플러그인
  (`caching_sha2_password`)을 쓰므로 8.4 업그레이드의 영향을 받지 않는다. 당시 앱 드라이버
  (PyMySQL 1.2.0 + cryptography)로 새 연결을 맺어 확인했다.
- 계정을 5.7 시절에 만들었거나 `--default-authentication-plugin=mysql_native_password`로
  운영했다면 그 계정은 8.4에서 로그인하지 못한다. 공식 문서는 이때 1045를 예로 들지만
  실측 오류는 1524였다. 조치는 둘 중 하나:
  - 권장: 8.0에서 미리 `ALTER USER '<user>'@'<host>' IDENTIFIED WITH caching_sha2_password BY '<pw>';`
  - 임시: 8.4를 `--mysql-native-password=ON`(또는 `[mysqld] mysql_native_password=ON`)으로 기동.
    9.0에서 플러그인이 제거되므로 임시 조치로만 쓴다
- `caching_sha2_password`는 TLS 없이 처음 접속할 때 RSA 키 교환이 필요하다. Go 드라이버
  (go-sql-driver/mysql 1.10)가 직접 처리하며, 새로 띄운 mysql:8.4 컨테이너에 `appuser`·root로 처음
  접속하는 통합 테스트와 스모크 테스트에서 확인했다(2026-11-15). 운영은 TLS 접속이라 해당하지 않는다.
