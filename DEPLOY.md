# 배포 가이드

## 개요

이 문서는 Jenkins를 사용하여 리눅스 서버에 백테스팅 플랫폼을 자동 배포하는 방법을 설명합니다.

## 사전 요구사항

### 서버 환경

1. **운영체제**: Linux (Ubuntu 20.04+ 권장)
2. **Docker**: 20.10 이상
3. **Docker Compose**: v2.0 이상
4. **Jenkins**: 2.300 이상

### 필수 설치

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose V2 설치 (이미 포함됨)
docker compose version

# Jenkins 사용자를 docker 그룹에 추가
sudo usermod -aG docker jenkins
```

## Jenkins 설정

### 1. Jenkins Job 생성

1. Jenkins 대시보드 → "새로운 Item"
2. 이름: `backtest-deploy`
3. 타입: **Pipeline**

### 2. Pipeline 설정

**General**:
- ✅ GitHub project: 리포지토리 URL 입력
- ✅ Discard old builds: 10개 유지

**Build Triggers**:
- ✅ GitHub hook trigger for GITScm polling (자동 배포)
- 또는 수동 배포: "Build Now" 사용

**Pipeline**:
- Definition: **Pipeline script from SCM**
- SCM: **Git**
  - Repository URL: `https://github.com/kyj0503/backtest.git`
  - Credentials: GitHub 인증 정보 추가
  - Branch: `*/deploy`
- Script Path: `Jenkinsfile`

### 3. 환경 변수 설정

Jenkins 서버의 `/home/jenkins/backtest/.env` 파일 생성:

```bash
# 배포 디렉토리 생성
sudo mkdir -p /home/jenkins/backtest
sudo chown -R jenkins:jenkins /home/jenkins/backtest

# .env 파일 생성
cd /home/jenkins/backtest
cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./backtest.db

# API Settings
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://your-server-ip:5173"]

# FastAPI
DEBUG=false

# Frontend
VITE_API_BASE_URL=/api
EOF
```

## 배포 파일 구조

```
backtest/
├── Jenkinsfile              # Jenkins 파이프라인 정의
├── compose.yaml             # 프로덕션 Docker Compose
├── compose.dev.yaml         # 개발 Docker Compose
├── .env                     # 환경 변수 (Git 제외)
├── backtest_be_fast/
│   └── Dockerfile           # Backend 프로덕션 이미지
└── backtest_fe/
    ├── Dockerfile           # Frontend 프로덕션 이미지
    └── Dockerfile.dev       # Frontend 개발 이미지
```

## 배포 프로세스

### 자동 배포 (GitHub Webhook)

1. GitHub 리포지토리 → Settings → Webhooks
2. Add webhook:
   - Payload URL: `http://your-jenkins-server/github-webhook/`
   - Content type: `application/json`
   - Events: `Just the push event`
3. `deploy` 브랜치에 push하면 자동 배포

### 수동 배포

1. Jenkins 대시보드 → `backtest-deploy` Job
2. **Build Now** 클릭
3. Console Output에서 진행 상황 확인

## 파이프라인 단계

| 단계 | 설명 | 소요 시간 |
|------|------|-----------|
| Preparation | 빌드 정보 출력 | 5초 |
| Checkout | Git 소스 체크아웃 | 10초 |
| Environment Check | Docker/Compose 버전 확인 | 5초 |
| Stop Old Containers | 기존 컨테이너 중지 | 10초 |
| Build Images | Docker 이미지 빌드 | 2-5분 |
| Deploy | 새 컨테이너 시작 | 30초 |
| Health Check | 서비스 상태 확인 | 1분 |
| Cleanup | 미사용 리소스 정리 | 10초 |

**총 예상 시간**: 약 5-7분

## 배포 후 확인

### 서비스 상태 확인

```bash
# 컨테이너 상태
docker compose ps

# 로그 확인
docker compose logs -f backtest-be-fast
docker compose logs -f backtest-fe

# 헬스체크
curl http://localhost:8000/api/v1/health
curl http://localhost:5173
```

### 서비스 접속

- **Frontend**: http://your-server-ip:5173
- **Backend API**: http://your-server-ip:8000
- **API Docs**: http://your-server-ip:8000/api/v1/docs

## 롤백

배포 실패 시 이전 버전으로 롤백:

```bash
# 1. 컨테이너 중지
docker compose down

# 2. 이전 브랜치로 체크아웃
git checkout <previous-commit-hash>

# 3. 재배포
docker compose up -d --build
```

또는 Jenkins에서 이전 빌드 재실행:
1. Jenkins → `backtest-deploy` → Build History
2. 이전 성공 빌드 선택 → **Rebuild**

## 트러블슈팅

### 1. Docker 권한 오류

```bash
# Jenkins 사용자를 docker 그룹에 추가
sudo usermod -aG docker jenkins

# Jenkins 재시작
sudo systemctl restart jenkins
```

### 2. 포트 충돌

```bash
# 포트 사용 중인 프로세스 확인
sudo lsof -i :8000
sudo lsof -i :5173

# 프로세스 종료
sudo kill -9 <PID>
```

### 3. 이미지 빌드 실패

```bash
# Docker 빌드 캐시 삭제
docker builder prune -a

# 수동 빌드 테스트
docker compose -f compose.yaml build --no-cache
```

### 4. Health Check 실패

```bash
# Backend 로그 확인
docker logs backtest-be-fast-prod

# 컨테이너 내부 접속
docker exec -it backtest-be-fast-prod /bin/bash

# 직접 헬스체크
curl http://localhost:8000/api/v1/health
```

## 모니터링

### 리소스 사용량

```bash
# CPU/메모리 사용량
docker stats

# 디스크 사용량
docker system df
```

### 로그 관리

```bash
# 실시간 로그
docker compose logs -f

# 최근 100줄
docker compose logs --tail=100

# 특정 서비스만
docker compose logs -f backtest-be-fast
```

## 보안 권장사항

1. **방화벽 설정**:
   ```bash
   # UFW 사용 예시
   sudo ufw allow 8000/tcp
   sudo ufw allow 5173/tcp
   ```

2. **환경 변수 보호**:
   - `.env` 파일 권한: `chmod 600 .env`
   - Git에 커밋하지 않기 (`.gitignore` 확인)

3. **HTTPS 설정** (Nginx 리버스 프록시 권장):
   - Let's Encrypt 인증서 사용
   - 80 → 443 리다이렉트

## 참고 자료

- [Docker Documentation](https://docs.docker.com/)
- [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/)
- [Docker Compose](https://docs.docker.com/compose/)
