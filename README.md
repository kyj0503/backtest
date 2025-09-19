- 스키마 구조는 `/database`에 있습니다.
- 환경파일:
  - `/backtest_fe`에 `.env` 생성 필요
  - `/backtest_be_fast`에 `.env` 생성 필요
  - `/backtest_be_spring`에 `.env` 생성 필요
---
- 개발 환경 실행:
  ```bash
  docker compose -f compose/compose.dev.yaml up -d --build
  ```
- 특정 컨테이너만 실행:
  ```bash
  docker compose -f compose/compose.dev.yaml up -d mysql
  ```
  - 기본적으로 도커 MySQL 컨테이너는 호스트의 `3307` 포트에 매핑됩니다. 이미 설치된 MySQL(3306)과 충돌하지 않도록 구성했으며, 필요 시 `MYSQL_HOST_PORT` 변수를 지정해 다른 포트로 노출할 수 있습니다.
- 프로덕션 환경 실행:
  ```bash
  docker compose -f compose/compose.prod.yaml up --build -d
  ```