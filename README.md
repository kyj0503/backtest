개발 스택 가이드

개발 시 Docker Compose로 FastAPI, 프론트엔드, MySQL, Redis를 관리한다. Spring Boot는 IDE에서 로컬로 실행한다.

실행
```bash
docker compose -f compose/compose.dev.yaml up -d --build
```

중지
```bash
docker compose -f compose/compose.dev.yaml down
```

완전 제거(컨테이너/이미지/볼륨)
```bash
# --rmi all, --volumes는 로컬 이미지와 볼륨을 제거한다
docker compose -f compose/compose.dev.yaml down --rmi all --volumes --remove-orphans
```

상태 확인
```bash
# 관련 컨테이너 상태 확인
docker ps --filter "name=backtest" --format "table {{.Names}}\t{{.Status}}"

# Compose 병합 설정 확인
docker compose -f compose/compose.dev.yaml config
```

개별 컨테이너 제어
```bash
# 서비스 단위 실행/중지/삭제
docker compose -f compose/compose.dev.yaml up -d backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml stop backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml rm -f backtest_be_fast backtest_fe mysql
```

환경 변수
- 개발은 루트 `.env.local`, 프로덕션은 루트 `.env`를 사용한다. 필요하면 `.env.example`을 복사해 값을 채운다.
```bash
cp .env.example .env.local
```
- Compose는 각 서비스에서 `env_file`로 루트 `.env.local` 또는 `.env`를 불러온다. 비밀 값은 커밋하지 않는다.

MySQL 인증 주의
- 개발용 Compose는 PyMySQL 호환을 위해 `mysql_native_password` 플러그인으로 기동한다. 기본 `caching_sha2_password`로 인한 인증 오류를 회피한다.

볼륨 정리
```bash
# 프로젝트 볼륨만 삭제
docker volume rm backtest_db_data_dev backtest_redis_data_dev backtest_fe_node_modules backtest_be_fast_venv || true

# 불필요 볼륨 정리(주의)
docker volume prune -f
```
