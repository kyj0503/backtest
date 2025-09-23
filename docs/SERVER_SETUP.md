# 서버 설정 가이드

## 1. 서버 환경 설정

### 필수 준비사항

```bash
# 서버에 SSH 접속 후

# 배포 디렉토리 생성
sudo mkdir -p /opt/backtest
sudo chown $USER:$USER /opt/backtest
cd /opt/backtest

# 프로젝트 클론
git clone https://github.com/capstone-backtest/backtest.git .

# 환경 파일 생성
cp .env.prod.example .env
```

### 2. .env 파일 설정 예시

`/opt/backtest/.env` 파일을 다음과 같이 설정하세요:

```bash
########################################
# Database Configuration
########################################
MYSQL_ROOT_PASSWORD=your_secure_mysql_password_123!
MYSQL_DATABASE=stock_community

########################################
# Redis Configuration  
########################################
REDIS_PASSWORD=your_secure_redis_password_456!

########################################
# JWT Security (최소 64바이트)
########################################
APP_SECURITY_JWT_SECRET=your_very_long_jwt_secret_at_least_64_bytes_for_hs512_algorithm_security_requirements_abcdefghijklmnopqrstuvwxyz1234567890
APP_SECURITY_JWT_ACCESS_TOKEN_EXPIRATION=PT15M
APP_SECURITY_JWT_REFRESH_TOKEN_EXPIRATION=P7D
APP_SECURITY_JWT_ISSUER=backtest-be-spring

########################################
# Application Security
########################################
SECRET_KEY=your_application_secret_key_for_fastapi_32_bytes_minimum_length
DATABASE_PASSWORD=your_secure_mysql_password_123!
DATABASE_NAME=stock_community

########################################
# Spring Boot Configuration
########################################
SPRING_DATASOURCE_PASSWORD=your_secure_mysql_password_123!
SPRING_DATASOURCE_POOL_SIZE=20
SPRING_REDIS_PASSWORD=your_secure_redis_password_456!

########################################
# Frontend Configuration
########################################
VITE_API_BASE_URL=/api

########################################
# Logging
########################################
LOG_LEVEL=INFO
```

### 3. 보안 키 생성

강력한 비밀번호와 키를 생성하려면:

```bash
# JWT 시크릿 (64바이트 이상)
openssl rand -base64 64

# 애플리케이션 시크릿 (32바이트)
openssl rand -base64 32

# 데이터베이스 비밀번호
openssl rand -base64 16 | tr -d "=+/" | cut -c1-16

# Redis 비밀번호  
openssl rand -base64 16 | tr -d "=+/" | cut -c1-16
```

### 4. GitHub Container Registry 설정

```bash
# Personal Access Token으로 로그인
echo "ghp_xxxxxxxxxxxxxxxxxxxx" | docker login ghcr.io -u your-github-username --password-stdin
```

### 5. 권한 설정

```bash
# .env 파일 보안 설정
chmod 600 /opt/backtest/.env

# 배포 스크립트 실행 권한
chmod +x /opt/backtest/scripts/deploy.sh

# Docker 그룹에 사용자 추가 (재로그인 필요)
sudo usermod -aG docker $USER
```

## GitHub Secrets 설정

Repository → Settings → Secrets and variables → Actions에서 다음만 설정:

```
DEPLOY_HOST=123.456.789.0
DEPLOY_USER=ubuntu  
DEPLOY_SSH_KEY=-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
DEPLOY_PORT=22
DEPLOY_PATH=/opt/backtest
GHCR_USERNAME=your-github-username
GHCR_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
```

## 배포 테스트

```bash
# 수동 배포 테스트
cd /opt/backtest
./scripts/deploy.sh

# 서비스 상태 확인
docker compose -f compose/compose.prod.yaml ps

# 로그 확인
docker compose -f compose/compose.prod.yaml logs -f
```

이제 `main` 브랜치에 푸시하면 자동으로 배포됩니다!