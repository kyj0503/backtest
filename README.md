```bash
# 개발 환경 실행
docker compose -f compose/compose.dev.yaml up -d --build

# 프로덕션 환경 실행
docker compose -f compose/compose.prod.yaml up -d --build 
```