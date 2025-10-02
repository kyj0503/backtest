개발 스택 가이드

개발/운영 모두 Docker Compose로 FastAPI, 프론트엔드, MySQL, Redis, Spring Boot를 함께 실행할 수 있다.

실행
```bash
# 주의: 항상 루트 디렉토리에서 실행해야 .env.local 파일이 로드됩니다
cd /home/kyj/backtest  # 또는 프로젝트 루트로 이동
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
- **모든 환경 변수는 루트 디렉토리의 `.env`와 `.env.local` 파일에서만 관리한다.**
- 서브 폴더(`backtest_be_fast/`, `backtest_be_spring/`, `backtest_fe/`, `compose/`)에는 `.env` 파일을 만들지 않는다.
- 개발은 루트 `.env.local`, 프로덕션은 루트 `.env`를 사용한다.

```bash
# 환경 파일 생성
cp .env.example .env.local

# 필수 시크릿 값 변경
nano .env.local  # SECRET_KEY, JWT_SECRET, PASSWORDS 등
```

- Compose는 각 서비스에서 `env_file: ../.env.local`로 루트 환경 파일을 불러온다.
- 모든 시크릿 값은 환경 변수로만 관리하며, 코드나 설정 파일에 초기값을 넣지 않는다.
- 자세한 내용은 [`ENV_GUIDE.md`](./ENV_GUIDE.md) 참조.

MySQL 인증 주의
- 개발용 Compose는 PyMySQL 호환을 위해 `mysql_native_password` 플러그인으로 기동한다. 기본 `caching_sha2_password`로 인한 인증 오류를 회피한다.

볼륨 정리
```bash
# 프로젝트 볼륨만 삭제
docker volume rm backtest_db_data_dev backtest_redis_data_dev backtest_fe_node_modules backtest_be_fast_venv || true

# 불필요 볼륨 정리(주의)
docker volume prune -f
```
