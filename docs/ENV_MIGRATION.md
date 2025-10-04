# 환경 설정 변경 사항 요약

## 변경 내용

### 1. 환경 변수 파일 통합 ✅

**변경 전:**
- `.env` (기본값)
- `.env.local` (개발 환경)

**변경 후:**
- `.env` (단일 파일로 통합)
- `.env.example` (템플릿)

**이유:**
- 관리 복잡도 감소
- `.env` 파일만 `.gitignore`에 추가하여 시크릿 보호
- 각 환경(개발/운영)에서 독립적으로 `.env` 관리

### 2. Compose 파일 업데이트 ✅

#### compose.dev.yaml (개발 환경)
- `env_file: ../.env.local` → `env_file: ../.env`
- MySQL, Redis 컨테이너 포함
- Docker 네트워크 사용 (bridge)

#### compose.prod.yaml (운영 환경 - Jenkins용)
- 호스트의 MySQL/Redis 사용
- `network_mode: host` 적용
- MySQL/Redis 컨테이너 제거

#### compose.server.yaml (운영 서버 전용 - 신규)
- `/opt/backtest/backend/` 디렉터리에서 독립 실행
- 같은 디렉터리의 `.env` 파일 사용
- Jenkins 없이도 스택 관리 가능

### 3. Windows WSL2 호환성 확인 ✅

**개발 환경 (compose.dev.yaml):**
- ✅ WSL2에서 정상 작동
- Bridge 네트워크 사용
- 모든 서비스 컨테이너로 실행

**운영 환경 (compose.prod.yaml, compose.server.yaml):**
- ⚠️ `network_mode: host`는 WSL2에서 제한적
- WSL2는 Linux VM이므로 호스트 네트워크 모드가 다르게 동작
- **권장:** 운영 서버는 네이티브 Linux 사용

**WSL2에서 운영 테스트가 필요한 경우:**
- compose.dev.yaml 형식 사용 (bridge 네트워크)
- 포트 매핑으로 서비스 노출

### 4. 운영 서버 구성 확인 ✅

**현재 상태:**
- ✅ `/opt/backtest/backend/.env` 파일만 존재
- ❌ compose 파일 없음 → **문제 발생**

**해결 방법:**
```bash
# 서버에서 실행
cd /opt/backtest/backend
wget https://raw.githubusercontent.com/capstone-backtest/backtest/main/compose/compose.server.yaml -O compose.yaml
```

**이제 가능한 작업:**
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

## Jenkins CI/CD 파이프라인 개선 ✅

**변경 사항:**
- `COMPOSE_FILE`: `compose/compose.prod.yaml` → `/opt/backtest/backend/compose.yaml`
- `ENV_FILE_PATH`: `/opt/backtest/backend/.env` (동일)
- Deploy 단계: 서버의 compose 파일 직접 사용

**파이프라인 동작:**
1. 이미지 빌드 (git 저장소에서)
2. 이미지를 레지스트리에 푸시
3. 운영 서버의 `/opt/backtest/backend/compose.yaml` 사용하여 배포
4. 헬스체크 수행

## 파일 구조

```
backtest/
├── .env                          # 환경 변수 (git에 추적 안됨)
├── .env.example                  # 환경 변수 템플릿 (git에 추적됨)
├── .gitignore                    # .env 제외 설정
├── README.md                     # 업데이트됨
├── DEPLOY.md                     # 운영 배포 가이드 (신규)
├── Jenkinsfile                   # 업데이트됨
└── compose/
    ├── compose.dev.yaml          # 개발 환경 (전체 스택)
    ├── compose.prod.yaml         # 운영 환경 (Jenkins용)
    └── compose.server.yaml       # 운영 서버 전용 (신규)

# 운영 서버:
/opt/backtest/backend/
├── .env                          # 운영 환경 변수
└── compose.yaml                  # compose.server.yaml 복사본
```

## 마이그레이션 가이드

### 개발 환경

```bash
# 1. .env.local 내용을 .env로 복사
cp .env.local .env

# 2. .env.local 삭제 (선택사항)
rm .env.local

# 3. 스택 재시작
docker compose -f compose/compose.dev.yaml down
docker compose -f compose/compose.dev.yaml up -d
```

### 운영 서버

```bash
# 1. 서버 접속
ssh your-server

# 2. compose 파일 복사
cd /opt/backtest/backend
wget https://raw.githubusercontent.com/capstone-backtest/backtest/main/compose/compose.server.yaml -O compose.yaml

# 3. .env 파일 확인 및 수정
nano .env
# 필수 항목 확인:
# - MYSQL_ROOT_PASSWORD
# - REDIS_PASSWORD
# - SECRET_KEY
# - APP_SECURITY_JWT_SECRET
# - DATABASE_HOST=localhost (중요!)
# - SPRING_DATASOURCE_HOST=localhost (중요!)
# - SPRING_REDIS_HOST=localhost (중요!)

# 4. 호스트 MySQL/Redis 상태 확인
sudo systemctl status mysql
sudo systemctl status redis

# 5. 스택 시작
docker compose up -d

# 6. 로그 확인
docker compose logs -f
```

## 검증 체크리스트

- [ ] 개발 환경: `.env` 파일로 정상 작동
- [ ] 운영 서버: `/opt/backtest/backend/compose.yaml` 존재
- [ ] 운영 서버: `/opt/backtest/backend/.env` 존재 및 올바른 설정
- [ ] 운영 서버: 호스트 MySQL 실행 중 (`sudo systemctl status mysql`)
- [ ] 운영 서버: 호스트 Redis 실행 중 (`sudo systemctl status redis`)
- [ ] Jenkins: 최신 Jenkinsfile 사용
- [ ] `.gitignore`: `.env` 파일 제외 확인

## 주의사항

1. **절대 `.env` 파일을 git에 커밋하지 마세요!**
2. **운영 환경에서는 반드시 강력한 시크릿 사용:**
   ```bash
   # JWT 시크릿 생성
   openssl rand -base64 64
   
   # 일반 시크릿 생성
   openssl rand -hex 32
   ```
3. **MySQL/Redis 비밀번호는 호스트 설치 시 설정한 것과 동일하게:**
   - `.env`의 `MYSQL_ROOT_PASSWORD`
   - `.env`의 `REDIS_PASSWORD`
4. **Windows WSL2에서 운영 환경 테스트 불가:**
   - 개발 환경만 WSL2에서 테스트
   - 운영 배포는 네이티브 Linux 서버 사용
