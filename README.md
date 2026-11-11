# Backtest — 라고할때살걸 백엔드

주식·암호화폐 전략 및 포트폴리오 백테스트를 제공하는 Rust(Axum/Tokio) 서비스입니다.
프론트엔드는 [backtest-console](https://github.com/kyj0503/backtest-console) 저장소로 분리했습니다.
기존 저장소 이름과 전체 Git 이력은 유지합니다.

## 구성

- `backtest_be_rust/`: Rust API, 계산 엔진, SQLx MySQL 저장소와 Docker 빌드.
- `backtest_be_fast/`: 이전 Python 구현, 비교 검증 기준 및 기존 Alembic 이력.
- `database/`: MySQL 스키마와 마이그레이션 운영 안내.
- `compose.dev.yaml`: 로컬 백엔드·MySQL 개발 환경.
- `compose.dev-prod.yaml`: 소스 마운트 없는 Rust 릴리스 이미지의 로컬 검증.
- `compose.yaml`, `scripts/deploy.*`, `.github/workflows/cicd.yml`: OCI 배포.
- `TODO.md`: 미완료 작업, `HISTORY.md`: 기존 구현·검증 이력.

## 로컬 개발

```bash
cp .env.example .env
docker compose -f compose.dev.yaml up -d --build
```

백엔드는 localhost:8000, 개발 MySQL은 127.0.0.1:3306입니다.
프론트엔드는 별도로 backtest-console 저장소의 `compose.dev.yaml`을 실행하면 localhost:5173에서 접속합니다.
`.env`의 DATABASE_*와 MySQL 사용자 설정은 서로 일치해야 합니다.
소스 변경 후 `docker compose -f compose.dev.yaml restart backtest-be`로 다시 컴파일합니다.
Rust 서버는 컨테이너당 단일 프로세스에서 Tokio 작업과 계산 스레드를 사용합니다.
Python 또는 Node 런타임은 백엔드 운영 이미지에 포함되지 않습니다.

기존 Python과 Rust를 동시에 비교하려면 PowerShell에서 `./scripts/start-local-comparison.ps1`을 실행합니다.
Python 화면은 `localhost:5173`, Rust 화면은 `localhost:5174`이며, 별도 DB 캐시를 사용합니다.
기준 커밋과 중지·재시작 명령은 [로컬 비교 환경](comparison/README.md)을 참조하세요.
환율·동작 차이 수정 후 [결과 및 성능](comparison/results-fixed-2026-11-11.md), [메모리 재측정](comparison/memory-results-fixed-2026-11-11.md)을 확인할 수 있습니다.

## 검증

```bash
docker build --target test ./backtest_be_rust
sh scripts/audit-deps.sh be
sh scripts/check-schema-parity.sh
docker build --target runtime ./backtest_be_rust
```

테스트는 Docker에서 실행합니다. 스키마 정합성 검사는 임시 MySQL만 사용하며 운영 DB를 변경하지 않습니다.
CI 취약점 검사는 알려진 취약점을 예외 없이 차단합니다.

## GitHub Actions 배포

- PR(main/dev): Docker 단위 테스트, 의존성 감사, 스키마 정합성, 런타임 빌드.
- main push/수동 실행: 검증 후 이미지를 게시하고 production에 배포합니다.
- dev push/수동 실행: CI 검증만 수행합니다. 별도의 OCI 개발 앱·DB는 운영하지 않으며 로컬 개발 Compose를 사용합니다.
- 게시 이미지: `ghcr.io/kyj0503/backtest`, 아키텍처: ARM64.
- 실행 커밋의 revision과 이미지 digest를 확인한 뒤 Tailscale을 통해 OCI에 배포합니다.
- OCI 컨테이너는 `backtest-be` 하나이며 공개 호스트 포트는 없습니다.
- 서버 경로는 `/opt/backtest/production`입니다.
- 서버 `.env`는 수동 관리하고 배포가 덮어쓰지 않습니다. `.env.production.example`에 필요한 항목을 기록했습니다.
- GitHub의 production Environment에는 `OCI_SSH_KEY` Secret 및 `OCI_HOST`, `OCI_USER`, `OCI_KNOWN_HOSTS`, `TS_CLIENT_ID`, `TS_AUDIENCE` Variables를 등록합니다.
- GHCR 인증은 자동 `GITHUB_TOKEN`, Tailscale 연결은 저장소·환경·브랜치·workflow로 제한한 OIDC를 사용합니다.
- Docker liveness `/health`와 DB readiness `/health/ready`를 모두 확인합니다. 실패하면 이전 릴리스를 복원하고 실행은 실패로 유지합니다.
- 공통 Nginx는 별도 `/opt/gateway`에서 관리합니다. 배포 후 `nginx-gateway` 설정 검사와 reload가 필요합니다.
- main 대상 PR은 사용자가 직접 병합합니다. 최초 환경 설정과 실제 배포 성공 전에는 전환 완료로 간주하지 않습니다.

## DB 운영

앱 배포에서 운영 DB 마이그레이션을 자동 실행하지 않습니다.
OCI 관리형 MySQL 26.10을 사용하며, 전용 CA를 검증하는 TLS 연결을 사용합니다.
CA 파일은 `/opt/backtest/production/tls/oracle-mysql-ca.pem`에 두고 컨테이너의 `/app/tls`에 읽기 전용으로 마운트합니다.
스키마 변경은 `database/schema.sql`과 `backtest_be_fast/alembic/`를 함께 갱신하고 검증합니다.
기존 DB의 baseline, Alembic 적용, MySQL 버전 변경은 [database/README.md](database/README.md)를 따릅니다.

개발 DB는 로컬 `compose.dev.yaml`에서만 실행합니다. 초기 SQL은 빈 볼륨에서만 적용됩니다.
기존 DB에 `schema.sql`을 다시 실행하거나 `down -v`로 보관할 데이터를 삭제하지 마세요.

## API와 프론트엔드 계약

`POST /api/v1/backtest`가 주요 API입니다. 최소 백테스트 기간은 30일입니다.

콘솔은 `include_*`를 끄고 계산 결과를 먼저 받은 뒤 `/api/v1/prices`, `/exchange-rates`,
`/benchmarks`, `/news`를 각각 조회·재시도합니다. 기존 POST 통합 응답은 기본 옵션으로 계속 지원합니다.
조회·취소·실행 한도와 이전 절차는 [API 경계](docs/architecture/api-boundaries.md)를 참고하세요.
프론트엔드의 `MIN_BACKTEST_PERIOD_DAYS`와 백엔드 설정을 함께 유지합니다.
CORS는 공통 Nginx에서 처리합니다. 서버 비밀값을 프론트엔드 `VITE_*` 변수에 넣지 않습니다.

[Rust 이전·검증 안내](docs/rust-migration.md) · [이전 백엔드 상세 문서](backtest_be_fast/docs/README.md) · [미완료 작업](TODO.md) · [변경 이력](HISTORY.md)
