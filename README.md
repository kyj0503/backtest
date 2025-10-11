개발 스택 가이드

개발/운영 모두 Docker Compose로 FastAPI 백엔드와 React 프론트엔드를 함께 실행할 수 있다.

실행
```bash
cd /backtest  # 또는 프로젝트 루트로 이동
docker compose -f compose.dev.yaml up -d --build
```

중지
```bash
docker compose -f compose.dev.yaml down
```

완전 제거(컨테이너/이미지/볼륨)
```bash
# --rmi all, --volumes는 로컬 이미지와 볼륨을 제거한다
docker compose -f compose.dev.yaml down --rmi all --volumes --remove-orphans
```

상태 확인
```bash
# 관련 컨테이너 상태 확인
docker ps --filter "name=backtest" --format "table {{.Names}}\t{{.Status}}"

# Compose 병합 설정 확인
docker compose -f compose.dev.yaml config
```

개별 컨테이너 제어
```bash
# 서비스 단위 실행/중지/삭제
docker compose -f compose.dev.yaml up -d backtest_be_fast backtest_fe
docker compose -f compose.dev.yaml stop backtest_be_fast backtest_fe
docker compose -f compose.dev.yaml rm -f backtest_be_fast backtest_fe
```

환경 변수
- **모든 환경 변수는 루트 디렉토리의 `.env` 파일에서만 관리한다.**
- 서브 폴더(`backtest_be_fast/`, `backtest_fe/`)에는 `.env` 파일을 만들지 않는다.
- `.env` 파일은 git에 추적되지 않으므로 각 환경에서 직접 생성해야 한다.

## 운영 서버 배포

운영 서버에서는 호스트에 설치된 데이터베이스를 사용합니다.

### 초기 설정 (1회만)

```bash
# 1. 운영 서버 디렉터리 생성
sudo mkdir -p /opt/backtest/backend
cd /opt/backtest/backend

# 2. 환경 파일 생성
sudo nano .env

# 3. compose 파일 복사 (git 저장소에서)
sudo cp /path/to/repo/compose.server.yaml ./compose.yaml
```

### 스택 관리

```bash
cd /opt/backtest/backend

# 스택 시작
docker compose up -d

# 스택 중지
docker compose down

# 스택 재시작
docker compose restart

# 로그 확인
docker compose logs -f

# 상태 확인
docker compose ps
```

### 이미지 업데이트

```bash
cd /opt/backtest/backend

# 최신 이미지 pull
docker compose pull

# 스택 재배포 (무중단)
docker compose up -d

# 또는 Jenkins CI/CD 파이프라인 사용
```

볼륨 정리
```bash
# 프로젝트 볼륨만 삭제
docker volume rm backtest_fe_node_modules backtest_be_fast_venv || true

# 불필요 볼륨 정리(주의)
docker volume prune -f
```

| 레이어 | Spring 비교 | 역할 |
| --- | --- | --- |
| api/ | @RestController | HTTP 요청/응답 처리 |
| schemas/ | DTO | API 입출력 모델 정의 |
| repositories/ | @Repository + 캐싱 로직 | 데이터 소스 추상화 + 캐싱 전략 |
| services/ | @Service | 비즈니스 로직 |

