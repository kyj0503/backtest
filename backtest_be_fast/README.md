Compose 사용법

간단한 Docker Compose 설정으로 로컬에서 개발/테스트용으로 서버를 실행합니다.

빌드 및 실행:

```bash
# 이미지 빌드 및 컨테이너 시작
docker compose -f compose.yaml up --build

# 백그라운드로 실행
docker compose -f compose.yaml up -d --build

# 로그 보기
docker compose -f compose.yaml logs -f web

# 중지 및 제거
docker compose -f compose.yaml down
```

환경 변수 예시/설명:

- `DEBUG`: `true`로 설정 시 `run_server.py`의 `reload`가 활성화됩니다 (개발 용도).
(Redis 관련 설정이 제거되었습니다.)

헬스체크 엔드포인트:

- `GET /health` — 서비스 상태 확인
