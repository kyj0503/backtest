# 배포 가이드

## GitHub Actions CI/CD 파이프라인

### 필요한 GitHub Secrets

Repository Settings > Secrets and variables > Actions에서 다음 시크릿을 설정하세요:

#### 서버 접속 정보
```
DEPLOY_HOST=your-server-ip-or-domain
DEPLOY_USER=your-server-username
DEPLOY_SSH_KEY=your-private-ssh-key
DEPLOY_PORT=22
DEPLOY_PATH=/opt/backtest
```

#### GitHub Container Registry 접속 정보
```
GHCR_USERNAME=your-github-username
GHCR_TOKEN=your-github-token-with-packages-read-permission
```

#### 알림 설정 (선택사항)
```
SLACK_WEBHOOK_URL=your-slack-webhook-url
```

> **주의**: 데이터베이스 비밀번호, JWT 시크릿 등 민감한 정보는 GitHub Secrets에 저장하지 않고 서버의 `.env` 파일에 직접 저장합니다.

### SSH 키 설정

1. **서버에서 SSH 키 쌍 생성**:
```bash
ssh-keygen -t rsa -b 4096 -C "github-actions@yourdomain.com"
```

2. **공개 키를 authorized_keys에 추가**:
```bash
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

3. **개인 키를 GitHub Secrets에 추가**:
```bash
cat ~/.ssh/id_rsa
# 출력 내용을 DEPLOY_SSH_KEY 시크릿으로 등록
```

## 서버 설정

### 1. 필수 소프트웨어 설치

**Ubuntu/Debian**:
```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose 설치 (최신 버전)
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 기타 유틸리티
sudo apt update
sudo apt install -y curl jq htop
```

**CentOS/RHEL**:
```bash
# Docker 설치
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 기타 유틸리티  
sudo dnf install -y curl jq htop
```

### 2. 배포 디렉토리 설정

```bash
# 배포 디렉토리 생성
sudo mkdir -p /opt/backtest
sudo chown $USER:$USER /opt/backtest
cd /opt/backtest

# GitHub 리포지토리 클론
git clone https://github.com/capstone-backtest/backtest.git .

# 환경 설정 파일 생성
cp .env.prod.example .env

# 환경 변수 편집 (실제 값으로 수정)
nano .env
```

### 3. GitHub Container Registry 인증

```bash
# Personal Access Token 생성 (GitHub Settings > Developer settings > Personal access tokens)
# Scopes: read:packages

# Docker 로그인
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

### 4. 초기 배포

```bash
# 수동 초기 배포
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# 또는 직접 실행
docker compose -f compose/compose.prod.yaml up -d
```

### 5. 네트워크 및 방화벽 설정

**포트 오픈**:
- 80 (HTTP)
- 443 (HTTPS) 
- 8080 (Spring Boot - 필요시)
- 8000 (FastAPI - 필요시)

**Ubuntu UFW**:
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**CentOS/RHEL firewalld**:
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 6. SSL/TLS 설정 (선택사항)

**Let's Encrypt with Certbot**:
```bash
# Certbot 설치
sudo snap install --classic certbot

# SSL 인증서 발급
sudo certbot certonly --webroot -w /opt/backtest/nginx/html -d yourdomain.com

# Nginx SSL 설정
sudo cp /etc/letsencrypt/live/yourdomain.com/*.pem /opt/backtest/nginx/ssl/

# 자동 갱신 설정
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 7. 모니터링 설정

**시스템 리소스 모니터링**:
```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker compose -f compose/docker-compose.prod.yml logs -f

# 시스템 리소스 확인
htop
df -h
```

**애플리케이션 모니터링**:
- Grafana: http://your-server:3001 (admin / GRAFANA_ADMIN_PASSWORD)
- Prometheus: http://your-server:9090

## 배포 워크플로우

### 자동 배포 (권장)

1. `main` 브랜치에 코드 푸시
2. GitHub Actions가 자동으로:
   - 테스트 실행
   - Docker 이미지 빌드 및 푸시
   - 서버에 자동 배포

### 수동 배포

```bash
# 서버에 SSH 접속
ssh user@your-server

# 배포 디렉토리로 이동
cd /opt/backtest

# 최신 이미지 풀 및 재배포
docker compose -f compose/compose.prod.yaml pull
docker compose -f compose/compose.prod.yaml up -d

# 또는 스크립트 사용
./scripts/deploy.sh
```

### 롤백 방법

```bash
# 이전 이미지로 롤백
docker compose -f compose/compose.prod.yaml down
docker tag ghcr.io/capstone-backtest/backtest/backtest-be-fast:previous-tag ghcr.io/capstone-backtest/backtest/backtest-be-fast:latest
docker compose -f compose/compose.prod.yaml up -d
```

## 트러블슈팅

### 일반적인 문제들

1. **컨테이너가 시작되지 않는 경우**:
```bash
# 로그 확인
docker compose -f compose/compose.prod.yaml logs [service-name]

# 컨테이너 상태 확인
docker ps -a
```

2. **데이터베이스 연결 실패**:
```bash
# MySQL 컨테이너 상태 확인
docker exec -it bt_mysql_prod mysql -u root -p -e "SHOW DATABASES;"

# 네트워크 확인
docker network ls
docker network inspect backtest-network-prod
```

3. **이미지 풀 실패**:
```bash
# GitHub Container Registry 로그인 확인
docker login ghcr.io

# 이미지 수동 풀
docker pull ghcr.io/capstone-backtest/backtest/backtest-be-fast:latest
```

4. **SSL 인증서 문제**:
```bash
# 인증서 갱신
sudo certbot renew

# Nginx 설정 확인
sudo nginx -t
```

### 로그 위치

- 애플리케이션 로그: `docker compose logs [service]`
- Nginx 로그: `/var/log/nginx/`
- 배포 로그: `/opt/backtest/logs/`

### 백업 및 복구

```bash
# 데이터베이스 백업
docker exec bt_mysql_prod mysqldump -u root -p[PASSWORD] --all-databases > backup-$(date +%Y%m%d).sql

# 볼륨 백업
docker run --rm -v backtest_db_data_prod:/data -v $(pwd):/backup alpine tar czf /backup/db-backup-$(date +%Y%m%d).tar.gz /data
```