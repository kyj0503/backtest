# Backtest — 라고할때살걸 백엔드

주식·암호화폐 전략 및 포트폴리오 백테스트 백엔드입니다. 같은 API를 세 언어로 구현해 두었고, 운영에
배포하는 것은 **Go**입니다(chi, 표준 net/http). 프론트엔드는
[backtest-console](https://github.com/kyj0503/backtest-console) 저장소로 분리했습니다.
Python(FastAPI) 원본에서 옮긴 과정과 계산 계약은 [docs/go-migration.md](docs/go-migration.md)에 있습니다.

## 구성

| 폴더 | 언어·스택 | 역할 |
|---|---|---|
| `backtest_be_go/` | Go 1.27, chi | **운영 배포 대상.** `cmd/server`, `cmd/backtestctl`(마이그레이션·점검), `migrations/`(goose, 스키마 소유), `testdata/`(고정 기준 자료) |
| `backtest_be_rust/` | Rust, Axum | rust-migration 구현. 정합성 수정 계약(F01–T05)의 원조이자 Go의 차등 비교 대상 |
| `backtest_be_python/` | Python 3.15, FastAPI | develop `b7a284f`의 원본 앱(옛 `backtest_be_fast`)에 Go 계산 엔진을 옮긴 구현(`app/engine/`) |

세 구현은 같은 계산 계약(asset_id, Time_Weighted_Return 등)과 같은 HTTP 입출력(스키마·키 순서·422 본문)을 따릅니다.
`scripts/conformance/run.sh`가 Python·Rust를 Go와 133개 사례로 비교합니다. 옛 Python 계산과의 차이는
docs/go-migration.md "Python(develop) 대비 바뀐 값"에 있습니다.

- `database/`: MySQL 스키마(`schema.sql` = goose head)와 마이그레이션 운영 안내. 스키마는 Go(goose)가 소유한다.
  Python의 `alembic/`은 이력이며 goose로 관리하는 DB에 실행하지 않는다.
- `compose.dev.yaml`: 언어별 개발 서버(프로필 `go` / `python` / `rust` / `all`) + MySQL.
- `compose.dev-prod.yaml`: 언어별 운영(runtime) 이미지 로컬 검증(같은 프로필).
- `compose.e2e.yaml`: 고정 시세 + 콘솔 + Playwright 브라우저 E2E(`E2E_BACKEND=go|rust`).
- `compose.bench.yaml`, `scripts/benchmark/`: 세 언어 고정 시세 성능 비교.
- `compose.conformance.yaml`, `scripts/conformance/`: 세 구현의 API 입출력 적합성 검사(Go 기준).
- `compose.loadtest.yaml`, `scripts/loadtest/`: k6 부하 테스트(구현별 CPU 2·2GiB, 한 번에 하나씩).
- `compose.devdb.yaml`, `scripts/load-devdb.sh`: 운영 DB 덤프의 로컬 검증용 복사본(덤프 파일은 커밋하지 않는다).
- `compose.yaml`, `scripts/deploy.*`, `.github/workflows/cicd.yml`: OCI 배포(Go).
- `TODO.md`: 미완료 작업, `HISTORY.md`: 구현·검증 이력.

## 로컬 개발

```bash
cp .env.example .env
docker compose -f compose.dev.yaml --profile go up -d --build        # Go     → localhost:8000
docker compose -f compose.dev.yaml --profile python up -d --build    # Python → localhost:8001
docker compose -f compose.dev.yaml --profile rust up -d --build      # Rust   → localhost:8002
docker compose -f compose.dev.yaml --profile all up -d --build       # 셋 다 함께
```

개발 MySQL은 127.0.0.1:3306이고 세 백엔드가 같이 씁니다. Go·Rust는 핫 리로드가 없어 코드를 바꾸면
`docker compose -f compose.dev.yaml restart backtest-be-go`(또는 `backtest-be-rust`)로 다시 컴파일합니다.
Python은 uvicorn `--reload`가 반영합니다.

프론트엔드는 backtest-console 저장소의 `compose.dev.yaml`을 실행하면 localhost:5173에서 접속합니다. 콘솔
프록시의 기본 대상 이름(`backtest-be-fast`)은 Go 서비스의 네트워크 별칭입니다. 다른 언어로 붙이려면 콘솔의
`BACKTEST_PROXY_TARGET`을 `http://backtest-be-python:8000` 또는 `http://backtest-be-rust:8000`으로 줍니다.
Python 원본의 응답은 콘솔 develop 브랜치, Go·Rust는 콘솔 rust-migration 브랜치와 짝입니다.

**빌드·실행·테스트는 모두 Docker로 합니다.** 호스트에 Go·Python·Rust 툴체인을 설치하지 않습니다.

## 검증

```bash
docker build --target test ./backtest_be_go          # gofmt, go vet, staticcheck, go test -race
docker build --target test ./backtest_be_python      # pytest 단위 + 골든 마스터
docker build --target test ./backtest_be_rust        # cargo fmt, clippy -D warnings, cargo test
bash scripts/test-go-integration.sh                  # Go 임시 MySQL 통합 테스트
sh scripts/audit-deps.sh all                         # govulncheck, pip-audit, cargo-audit
sh scripts/check-schema-parity.sh                    # schema.sql = goose head (COMMENT까지)
docker compose -f compose.e2e.yaml up --build --abort-on-container-exit --exit-code-from e2e
bash scripts/benchmark/run.sh                        # 세 언어 성능 비교(입력은 로컬 .comparison)
bash scripts/conformance/run.sh                     # API 입출력 적합성(Python·Rust vs Go)
bash scripts/loadtest/run.sh                        # k6 부하 테스트(입력은 로컬 .comparison)
```

모두 임시 컨테이너만 쓰고 운영 DB를 바꾸지 않습니다. 계산 정확성의 기준은 불변식 테스트(현금 보존,
체결 인과성, 수수료·손익 항등식)와 손으로 계산한 원장 사례입니다. Python 출력은 회귀 기록일 뿐입니다
(`backtest_be_go/testdata/README.md`). Rust 구현과의 차등 비교는 `scripts/diff-rust-reference.sh`.

## GitHub Actions 배포

- PR(main/develop): Docker 테스트, MySQL 통합 테스트, 의존성 감사, 스키마 정합성, 런타임 빌드.
- main push/수동 실행: 검증 후 이미지를 게시하고 production에 배포합니다.
- develop push: CI 검증만 수행합니다. OCI 개발 앱·DB는 없고 로컬 Compose를 사용합니다.
- 게시 이미지: `ghcr.io/kyj0503/backtest`, 아키텍처: ARM64, distroless(정적 바이너리 두 개).
- 실행 커밋의 revision과 이미지 digest를 확인한 뒤 Tailscale을 통해 OCI에 배포합니다.
- OCI 컨테이너는 `backtest-be` 하나이며 공개 호스트 포트는 없습니다. 서버 경로는 `/opt/backtest/production`입니다.
- 서버 `.env`는 수동 관리하고 배포가 덮어쓰지 않습니다. `.env.production.example`에 필요한 항목을 기록했습니다.
- GitHub의 production Environment에는 `OCI_SSH_KEY` Secret 및 `OCI_HOST`, `OCI_USER`, `OCI_KNOWN_HOSTS`,
  `TS_CLIENT_ID`, `TS_AUDIENCE` Variables를 등록합니다.
- Docker liveness `/health`와 DB readiness `/health/ready`를 모두 확인합니다(`/app/server -healthcheck <path>`,
  런타임 이미지에 curl이 없습니다). 실패하면 이전 릴리스를 복원하고 실행은 실패로 유지합니다.
- 공통 Nginx는 별도 `/opt/gateway`에서 관리합니다. 배포 후 `nginx-gateway` 설정 검사와 reload가 필요합니다.
- main 대상 PR은 사용자가 직접 병합합니다.

## DB 운영

앱 배포에서 운영 DB 마이그레이션을 자동 실행하지 않습니다. OCI 관리형 MySQL을 쓰며 전용 CA로 체인을
검증하는 TLS로 접속합니다. CA 파일은 `/opt/backtest/production/tls/oracle-mysql-ca.pem`에 두고 컨테이너의
`/app/tls`에 읽기 전용으로 마운트합니다(`DATABASE_SSL_CA` 또는 `DATABASE_URL`의 `ssl_ca`).

스키마 변경은 `database/schema.sql`과 `backtest_be_go/migrations/`의 새 goose 파일을 함께 고치고
`scripts/check-schema-parity.sh`로 확인합니다. Python 시절 DB의 전환(`backtestctl migrate detect / baseline /
up`)은 [database/README.md](database/README.md)를 따릅니다.

개발 DB는 로컬 `compose.dev.yaml`에서만 실행합니다. 초기 SQL은 빈 볼륨에서만 적용됩니다.
기존 DB에 `schema.sql`을 다시 실행하거나 `down -v`로 보관할 데이터를 삭제하지 마세요.

## API와 프론트엔드 계약

`POST /api/v1/backtest`가 주요 API입니다. 최소 백테스트 기간은 30일입니다. 응답 필드와 계산 정의는
rust-migration에서 정합성을 고친 계약(asset_id, Time_Weighted_Return, calculation_assumptions 등)을 따르므로
콘솔은 그 계약을 반영한 브랜치(backtest-console rust-migration)를 씁니다.

콘솔은 `include_*`를 끄고 계산 결과를 먼저 받은 뒤 `/api/v1/prices`, `/exchange-rates`, `/benchmarks`,
`/news`를 각각 조회·재시도합니다. 기존 POST 통합 응답은 기본 옵션으로 계속 지원합니다. 조회·취소·실행
한도는 [API 경계](docs/architecture/api-boundaries.md)를 참고하세요. 프론트엔드의 `MIN_BACKTEST_PERIOD_DAYS`와
백엔드 설정을 함께 유지합니다. CORS는 공통 Nginx에서 처리합니다. 서버 비밀값을 프론트엔드 `VITE_*` 변수에
넣지 않습니다.

[Go 전환 문서](docs/go-migration.md) · [미완료 작업](TODO.md) · [변경 이력](HISTORY.md)
