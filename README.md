- 스키마 구조는 `/database`에 있습니다.
- 환경파일:
  - `/backtest_fe`에 `.env` 생성 필요
  - `/backtest_be_fast`에 `.env` 생성 필요
  - `/backtest_be_spring`에 `application.properties` 생성 필요
---
- 개발 환경 실행:
  ```bash
  docker compose -f compose/compose.dev.yaml up --build -d
  ```
- 테스트 환경 실행:
  ```bash
  docker compose -f compose/compose.test.yaml up --build -d
  ```
- 프로덕션 환경 실행:
  ```bash
  docker compose -f compose/compose.prod.yaml up --build -d
  ```