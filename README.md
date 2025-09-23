간단 사용법

! 스프링부트 백엔드 개발 환경은 직접 인텔리제이에서 실행할 것
FastAPI 백엔드, React 프론트엔드, MySQL, Redis만 Docker Compose 스택으로 관리한다.

실행
```bash
docker compose -f compose/compose.dev.yaml up -d --build
```

환경 변수 설정
- 개발 및 프로덕션: 루트의 `.env` 파일을 사용합니다. 개발용 예제가 있으면 `.env.example`을 복사해서 `.env`로 만들고 필요한 값을 채워 주세요.
	```bash
	cp .env.example .env
	# 편집: vi .env 또는 에디터에서 수정
	```
Compose 파일은 각 서비스의 `env_file`을 통해 루트 `.env`를 불러오도록 구성되어 있습니다. 비밀 값은 로컬에서만 유지하고 리포지토리에 직접 커밋하지 마세요.

MySQL 인증 관련 주의사항
- 개발용 Compose는 FastAPI(PyMySQL)와의 호환성을 위해 MySQL을 `mysql_native_password` 인증 플러그인으로 시작하도록 설정되어 있습니다. 이는 일부 환경에서 기본 `caching_sha2_password`로 인한 인증 오류(예: RSA 키 교환 문제)를 예방하기 위한 조치입니다.

중지
```bash
docker compose -f compose/compose.dev.yaml down
```

완전 제거(컨테이너/이미지/볼륨)
```bash
# 주의: --rmi all, --volumes 플래그는 로컬 이미지와 볼륨을 제거합니다.
docker compose -f compose/compose.dev.yaml down --rmi all --volumes --remove-orphans
```

볼륨 정리
```bash
# Compose에서 사용하는 볼륨만 삭제 (필요 시 이름을 조정)
docker volume rm backtest_db_data_dev backtest_redis_data_dev \
	backtest_fe_node_modules backtest_be_fast_venv || true

# 전체 불필요 볼륨 정리 (주의)
docker volume prune -f
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
# 컨테이너 이름(Compose 서비스명)으로 개별 실행/중지/삭제
docker compose -f compose/compose.dev.yaml up -d backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml stop backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml rm -f backtest_be_fast backtest_fe mysql
```