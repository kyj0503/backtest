# 운영 서버 배포 가이드

## 사전 준비

### 1. 호스트에 MySQL 설치 및 설정

```bash
# MySQL 8.0 설치 (Ubuntu)
sudo apt update
sudo apt install mysql-server -y

# MySQL 보안 설정
sudo mysql_secure_installation

# MySQL 설정
sudo mysql -u root -p

# 필요한 데이터베이스 생성
CREATE DATABASE IF NOT EXISTS stock_data_cache CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS stock_community CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 권한 설정
GRANT ALL PRIVILEGES ON stock_data_cache.* TO 'root'@'localhost';
GRANT ALL PRIVILEGES ON stock_community.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 초기 스키마 적용 (git 저장소에서)
mysql -u root -p stock_data_cache < /path/to/repo/database/01_schema.sql
mysql -u root -p stock_data_cache < /path/to/repo/database/02_yfinance.sql
```

### 2. 호스트에 Redis 설치 및 설정

```bash
# Redis 설치 (Ubuntu)
sudo apt update
sudo apt install redis-server -y

# Redis 설정
sudo nano /etc/redis/redis.conf
# 다음 항목 수정:
# bind 127.0.0.1 ::1
# requirepass your-secure-redis-password

# Redis 재시작
sudo systemctl restart redis
sudo systemctl enable redis

# Redis 연결 테스트
redis-cli -a your-secure-redis-password ping
# PONG 응답이 와야 함
```

### 3. Docker 및 Docker Compose 설치

```bash
# Docker 설치 (Ubuntu)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose 설치 (V2)
# 최신 Docker Desktop 또는 Docker Engine에 포함되어 있음
docker compose version
```

## 초기 배포 설정

### 1. 배포 디렉터리 생성

```bash
sudo mkdir -p /opt/backtest/backend
sudo chown -R $USER:$USER /opt/backtest
cd /opt/backtest/backend
```

### 2. 환경 파일 생성

```bash
cd /opt/backtest/backend
nano .env
```

**`.env` 파일 내용 (예시):**

```bash
########################################
# FastAPI
########################################
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-production-secret-key-change-me

DEFAULT_INITIAL_CASH=10000.0
MAX_BACKTEST_DURATION_DAYS=3650
DEFAULT_COMMISSION=0.002

MAX_OPTIMIZATION_ITERATIONS=1000
OPTIMIZATION_TIMEOUT_SECONDS=300

YAHOO_FINANCE_TIMEOUT=30

NAVER_CLIENT_ID=your-naver-client-id
NAVER_CLIENT_SECRET=your-naver-client-secret

BACKEND_CORS_ORIGINS=http://your-domain.com,https://your-domain.com

# 호스트 MySQL 사용
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=root
DATABASE_PASSWORD=your-mysql-password
DATABASE_NAME=stock_data_cache
DATABASE_URL=mysql+pymysql://root:your-mysql-password@localhost:3306/stock_data_cache?charset=utf8mb4

########################################
# Frontend
########################################
VITE_API_BASE_URL=/api

########################################
# Spring Boot
########################################
# 호스트 MySQL 사용
SPRING_DATASOURCE_HOST=localhost
SPRING_DATASOURCE_PORT=3306
SPRING_DATASOURCE_USERNAME=root
SPRING_DATASOURCE_PASSWORD=your-mysql-password
SPRING_DATASOURCE_POOL_SIZE=20

# JWT - 운영용 시크릿 생성: openssl rand -base64 64
APP_SECURITY_JWT_SECRET=your-production-jwt-secret-at-least-64-bytes
APP_SECURITY_JWT_ACCESS_TOKEN_EXPIRATION=PT15M
APP_SECURITY_JWT_REFRESH_TOKEN_EXPIRATION=P7D
APP_SECURITY_JWT_ISSUER=backtest-be-spring

# 호스트 Redis 사용
SPRING_REDIS_HOST=localhost
SPRING_REDIS_PORT=6379
SPRING_REDIS_PASSWORD=your-redis-password

########################################
# Redis
########################################
REDIS_PASSWORD=your-redis-password

########################################
# MySQL
########################################
MYSQL_ROOT_PASSWORD=your-mysql-password
MYSQL_DATABASE=stock_data_cache
```

### 3. Compose 파일 복사

```bash
cd /opt/backtest/backend

# git 저장소에서 복사
cp /path/to/repo/compose/compose.server.yaml ./compose.yaml

# 또는 직접 다운로드
wget https://raw.githubusercontent.com/capstone-backtest/backtest/main/compose/compose.server.yaml -O compose.yaml
```

### 4. 이미지 Pull 및 스택 시작

```bash
cd /opt/backtest/backend

# 이미지 pull
docker compose pull

# 스택 시작
docker compose up -d

# 로그 확인
docker compose logs -f

# 상태 확인
docker compose ps
```

## 일상 운영

### 스택 관리 명령어

```bash
cd /opt/backtest/backend

# 스택 시작
docker compose up -d

# 스택 중지
docker compose down

# 스택 재시작
docker compose restart

# 특정 서비스만 재시작
docker compose restart backtest_be_spring

# 로그 확인
docker compose logs -f

# 특정 서비스 로그만 확인
docker compose logs -f backtest_be_fast
```

### 업데이트 배포

#### 방법 1: Jenkins CI/CD (권장)

Jenkins 파이프라인이 자동으로:
1. 이미지 빌드
2. 레지스트리에 푸시
3. 운영 서버에서 pull 및 재배포

#### 방법 2: 수동 배포

```bash
cd /opt/backtest/backend

# 최신 이미지 pull
docker compose pull

# 스택 재배포 (변경된 이미지만 재시작)
docker compose up -d

# 또는 강제 재생성
docker compose up -d --force-recreate
```

### 헬스체크

```bash
# FastAPI 헬스체크
curl http://localhost:8000/health

# Spring Boot 헬스체크
curl http://localhost:8080/actuator/health

# 프론트엔드 확인
curl http://localhost:80/
```

### 문제 해결

#### 컨테이너가 시작되지 않는 경우

```bash
# 로그 확인
docker compose logs

# 특정 서비스 로그 확인
docker compose logs backtest_be_spring

# 컨테이너 상태 확인
docker compose ps -a

# 강제 재시작
docker compose down
docker compose up -d
```

#### 데이터베이스 연결 실패

```bash
# MySQL 상태 확인
sudo systemctl status mysql

# MySQL 연결 테스트
mysql -u root -p -e "SHOW DATABASES;"

# Redis 상태 확인
sudo systemctl status redis
redis-cli -a your-password ping
```

#### 이미지 업데이트 안됨

```bash
# 캐시 무시하고 pull
docker compose pull --ignore-pull-failures

# 또는 이미지 직접 pull
docker pull ghcr.io/capstone-backtest/backtest/backtest-be-fast:latest
docker pull ghcr.io/capstone-backtest/backtest/backtest-be-spring:latest
docker pull ghcr.io/capstone-backtest/backtest/backtest-fe:latest
```

## 보안 고려사항

1. **방화벽 설정**
   ```bash
   # UFW 사용 시
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 8000/tcp  # 필요시
   sudo ufw allow 8080/tcp  # 필요시
   ```

2. **시크릿 관리**
   - `.env` 파일 권한 제한: `chmod 600 .env`
   - 운영 환경 시크릿은 절대 git에 커밋하지 않음
   - 정기적으로 JWT 시크릿 및 비밀번호 변경

3. **HTTPS 설정**
   - Nginx를 reverse proxy로 사용
   - Let's Encrypt로 SSL 인증서 발급

## Windows WSL2 환경

WSL2 환경에서도 동일한 방법으로 작동합니다:

```bash
# WSL2에서 Docker Desktop 사용
# Windows용 Docker Desktop 설치 후 WSL2 통합 활성화

cd /opt/backtest/backend
docker compose up -d
```

**주의사항:**
- `network_mode: host`는 WSL2에서 제한적으로 작동할 수 있음
- 필요시 개발 환경처럼 bridge 네트워크 사용 고려
