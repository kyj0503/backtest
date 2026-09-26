# database — 스키마와 MySQL 운영 가이드

캐시 DB(`stock_data_cache`)의 스키마 정의 두 경로와, MySQL 8.0 데이터 볼륨을 8.4로
올리는 절차를 적는다. 여기 적힌 수치와 로그는 2026-09-27 로컬 Docker 실측값이다
(mysql:8.0.46 → mysql:8.4.11).

## 스키마 정의는 두 곳에 있다

| 경로 | 언제 쓰나 | 파일 |
|---|---|---|
| initdb | 빈 데이터 디렉터리로 MySQL 컨테이너를 **처음** 띄울 때 공식 이미지가 1회 실행 | `database/schema.sql` (compose가 `/docker-entrypoint-initdb.d/01-schema.sql`로 마운트) |
| Alembic | 이미 떠 있는 DB에 이후 변경을 적용 | `backtest_be_fast/alembic/versions/` |

ORM 메타데이터가 없어 autogenerate를 쓸 수 없으므로 두 정의는 사람이 맞춘다.
스키마를 바꿀 때는 **schema.sql과 새 Alembic 리비전을 함께** 고치고 아래 검사로
확인한다. 기존 리비전은 고치지 않는다(이미 적용된 DB와 이력이 어긋난다).

### 정합성 검사: `scripts/check-schema-parity.sh`

```bash
scripts/check-schema-parity.sh                      # 기본: docker, mysql:8.4
DOCKER=docker.exe scripts/check-schema-parity.sh    # WSL에서 Windows Docker CLI 사용
```

빈 MySQL 두 개에 각각 schema.sql initdb와 `alembic upgrade head`를 적용하고, DB 기본
charset·테이블 목록·세 테이블의 `SHOW CREATE TABLE`(컬럼·테이블 COMMENT 포함)을 비교한다.
다르면 diff를 출력하고 종료 코드 1, 같으면 0. 임시 컨테이너·네트워크는 항상 정리한다.
바인드 마운트와 호스트 포트를 쓰지 않으므로 Jenkins(컨테이너 안에서 호스트 데몬 사용)에서도
그대로 돌 수 있다. Alembic 컨테이너가 `requirements.lock.txt`의 고정 버전을 pip로 받으므로
인터넷이 필요하다. 이미지가 캐시돼 있으면 한 번 실행에 약 20초 걸린다.

주의할 점:

- **컬럼 설명은 `--` 주석이 아니라 `COMMENT` 절로** 쓴다. Alembic 리비전이 같은 문구를
  COMMENT로 만들기 때문이다.
- **schema.sql 맨 위의 `SET NAMES utf8mb4;`를 지우지 말 것.** 공식 mysql 이미지의 initdb는
  POSIX 로케일의 mysql 클라이언트로 스크립트를 실행하며, 그 연결 문자셋은 `latin1`이다
  (실측: `character_set_client=latin1`). 이 줄이 없으면 한글 COMMENT가 이중 인코딩돼
  `'주식'`이 `'ì£¼ì‹'`로 저장된다. 이 줄을 빼면 정합성 검사가 실패한다.

### 기존 DB에 Alembic 적용

| DB가 만들어진 방식 | 적용 명령 |
|---|---|
| 현재 schema.sql로 initdb | `alembic stamp head` (이미 head와 같다) |
| 물리 FK 제거(A-10, `7b2e9c4f1a30`) **이전** schema.sql로 initdb | `alembic stamp d5c3763b29e6` → `alembic upgrade head` |
| 이미 Alembic 관리 중(운영 DB 포함) | `alembic upgrade head` |

`stamp head`를 FK가 남은 DB에 쓰면 FK 제거 리비전이 건너뛰어진다. Alembic은 파이프라인이나
운영 이미지가 실행하지 않으므로 수동으로 적용한다(`backtest_be_fast/`에서
`DATABASE_URL=... alembic upgrade head`).

`1f574a9ba22e`(2026-09-27)는 `daily_prices.stock_id` 컬럼 COMMENT만 바꾼다(`'stocks 테이블의
ID (Foreign Key)'` → `'stocks.id 논리 참조 (물리 FK 없음)'`). InnoDB 메타데이터 변경이라
테이블을 다시 쓰지 않는다(`ALGORITHM=INSTANT` 허용, `TOTAL_ROW_VERSIONS` 0 유지 확인).

### 기존 DB의 COMMENT는 저장소 정의와 다를 수 있다

2026-09-27 이전 schema.sql로 initdb한 DB(dev 볼륨, 운영 DB)는 COMMENT가 저장소 정의와 다르다.
동작에는 영향이 없다.

- 테이블 COMMENT 3개와 COMMENT가 있던 컬럼 5개가 위의 이중 인코딩 상태다
- 나머지 컬럼은 COMMENT가 없다(당시 schema.sql은 `--` 주석만 썼다)

맞추려면 각 컬럼 정의를 그대로 다시 적는 `MODIFY COLUMN`이 필요해, 운영 DB의
`SHOW CREATE TABLE`을 먼저 떠서 저장소 정의와 비교한 뒤에 진행한다(자동 리비전으로 넣지 않았다).

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
5. 테이블·행 수·제약 확인 후, 스키마가 A-10 이전 상태라면 위 표대로 Alembic 적용

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
- Alembic: `stamp d5c3763b29e6` → `upgrade head`로 `7b2e9c4f1a30`(FK 제거)와 `1f574a9ba22e`가
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
  (`caching_sha2_password`)을 쓰므로 8.4 업그레이드의 영향을 받지 않는다. 앱과 같은 드라이버
  (PyMySQL 1.2.0 + cryptography)로 새 연결을 맺어 확인했다.
- 계정을 5.7 시절에 만들었거나 `--default-authentication-plugin=mysql_native_password`로
  운영했다면 그 계정은 8.4에서 로그인하지 못한다. 공식 문서는 이때 1045를 예로 들지만
  실측 오류는 1524였다. 조치는 둘 중 하나:
  - 권장: 8.0에서 미리 `ALTER USER '<user>'@'<host>' IDENTIFIED WITH caching_sha2_password BY '<pw>';`
  - 임시: 8.4를 `--mysql-native-password=ON`(또는 `[mysqld] mysql_native_password=ON`)으로 기동.
    9.0에서 플러그인이 제거되므로 임시 조치로만 쓴다
- `caching_sha2_password`는 TLS 없이 처음 접속할 때 RSA 키 교환이 필요해 PyMySQL에
  `cryptography` 패키지가 있어야 한다. BE 락 파일에 이미 포함돼 있다
  (`requirements.lock.txt`의 `cryptography==50.0.0`).
