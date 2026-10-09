# Backtest — 라고할때살걸 백엔드

주식·암호화폐 전략 및 포트폴리오 백테스트를 제공하는 FastAPI 서비스입니다.
프론트엔드는 [backtest-console](https://github.com/kyj0503/backtest-console) 저장소로 분리했습니다.
기존 저장소 이름과 전체 Git 이력은 유지합니다.

## 구성

- `backtest_be_fast/`: Python 3.11, FastAPI, SQLAlchemy, pandas, backtesting.py 0.3.3.
- `database/`: MySQL 스키마와 마이그레이션 운영 안내.
- `compose.dev.yaml`: 로컬 백엔드·MySQL 개발 환경.
- `compose.dev-prod.yaml`: 실제 런타임 이미지의 로컬 워커 모드 검증.
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

## 검증

```bash
docker build --target test ./backtest_be_fast
sh scripts/audit-deps.sh be
sh scripts/check-schema-parity.sh
docker build --target runtime ./backtest_be_fast
```

테스트는 Docker에서 실행합니다. 스키마 정합성 검사는 임시 MySQL만 사용하며 운영 DB를 변경하지 않습니다.
CI 취약점 검사는 기존 bokeh 예외 근거를 유지합니다. 신규 차단 취약점을 무시하지 않습니다.

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
스키마 변경은 `database/schema.sql`과 `backtest_be_fast/alembic/`를 함께 갱신하고 검증합니다.
기존 DB의 baseline, Alembic 적용, MySQL 버전 변경은 [database/README.md](database/README.md)를 따릅니다.

개발 DB는 로컬 `compose.dev.yaml`에서만 실행합니다. 초기 SQL은 빈 볼륨에서만 적용됩니다.
기존 DB에 `schema.sql`을 다시 실행하거나 `down -v`로 보관할 데이터를 삭제하지 마세요.

## API와 프론트엔드 계약

`POST /api/v1/backtest`가 주요 API입니다. 최소 백테스트 기간은 30일입니다.
프론트엔드의 `MIN_BACKTEST_PERIOD_DAYS`와 백엔드 설정을 함께 유지합니다.
CORS는 공통 Nginx에서 처리합니다. 서버 비밀값을 프론트엔드 `VITE_*` 변수에 넣지 않습니다.

[백엔드 상세 문서](backtest_be_fast/docs/README.md) · [미완료 작업](TODO.md) · [변경 이력](HISTORY.md)
