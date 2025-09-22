간단 사용법

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
# 주의: --rmi all, --volumes 플래그는 로컬 이미지와 볼륨을 제거합니다.
docker compose -f compose/compose.dev.yaml down --rmi all --volumes --remove-orphans
```

볼륨 정리
```bash
# Compose에서 사용하는 볼륨만 삭제 (필요 시 이름을 조정)
docker volume rm backtest_db_data_dev backtest_redis_data_dev \
	backtest_fe_node_modules backtest_be_fast_venv backtest_be_spring_gradle_cache || true

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
docker compose -f compose/compose.dev.yaml up -d backtest_be_spring backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml stop backtest_be_spring backtest_be_fast backtest_fe mysql
docker compose -f compose/compose.dev.yaml rm -f backtest_be_spring backtest_be_fast backtest_fe mysql
```