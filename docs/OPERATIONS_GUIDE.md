# 운영 가이드

이 문서는 백테스팅 시스템의 배포, 운영, 모니터링에 필요한 모든 정보를 제공합니다.

## 목차

1. [배포 환경](#배포-환경)
2. [데이터 관리](#데이터-관리)
3. [CI/CD 파이프라인](#cicd-파이프라인)
4. [모니터링 및 헬스체크](#모니터링-및-헬스체크)
5. [트러블슈팅](#트러블슈팅)
6. [백업 및 복구](#백업-및-복구)

## 배포 환경

### 프로덕션 배포
```bash
# 프로덕션 환경 시작
docker compose -f compose/compose.prod.yml up -d

# 로그 확인
docker compose -f compose/compose.prod.yml logs -f

# 서비스 재시작
docker compose -f compose/compose.prod.yml restart backend
```

### 환경별 설정

#### 개발 환경
```bash
# 파일: compose.yml + compose/compose.dev.yml
docker compose -f compose.yml -f compose/compose.dev.yml up --build
```
- 백엔드: `localhost:8001`
- 프론트엔드: `localhost:5174` (Vite 개발 서버)
- 핫 리로드 활성화

#### 프로덕션 환경
```bash
# 파일: compose/compose.prod.yml
docker compose -f compose/compose.prod.yml up -d
```
- 백엔드: `localhost:8001`
- 프론트엔드: `localhost:8082` (Nginx)
- 최적화된 빌드

### 환경변수 설정

#### 필수 환경변수
```bash
# 데이터베이스
DATABASE_URL=mysql+pymysql://username:password@host:port/database

# CORS 설정
BACKEND_CORS_ORIGINS=["https://yourdomain.com"]

# 보안
SECRET_KEY=your-secret-key-here

# Redis (채팅용)
REDIS_URL=redis://redis:6379/0
```

#### 선택적 환경변수
```bash
# 네이버 뉴스 API
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# 로그 레벨
LOG_LEVEL=INFO

# 프론트엔드 API URL
VITE_API_BASE_URL=https://api.yourdomain.com
```

## 데이터 관리

### 데이터베이스 구조
시스템은 두 개의 분리된 MySQL 데이터베이스를 사용합니다:

1. **Community DB**: 사용자, 게시글, 댓글, 백테스트 히스토리
2. **Stock Data Cache DB**: 주가 데이터, 배당, 환율 정보

### 데이터 소스 전략
```
요청 → DB 캐시 확인 → 있으면 반환
                  → 없으면 yfinance 조회 → DB 저장 → 반환
```

#### 캐시 정책
- **우선순위**: MySQL DB 캐시 → yfinance API
- **자동 저장**: API에서 조회한 데이터는 자동으로 DB에 저장
- **보강 로직**: 부분적 누락 구간은 자동으로 보강

#### 데이터 품질 관리
```sql
-- 데이터 품질 확인
SELECT 
    ticker,
    COUNT(*) as records,
    MIN(date) as start_date,
    MAX(date) as end_date,
    AVG(CASE WHEN data_quality = 'good' THEN 1 ELSE 0 END) as quality_ratio
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.id
GROUP BY ticker
ORDER BY records DESC;
```

### 데이터베이스 초기화
```bash
# Community DB 초기화
mysql -u root -p < database/schema.sql

# Stock Data Cache DB 초기화  
mysql -u root -p < database/yfinance.sql

# 마이그레이션 실행 (멱등성 보장)
mysql -u root -p < database/yfinance_migration_001.sql
```

### 데이터 백업
```bash
# 전체 백업
mysqldump -u root -p --all-databases > backup_$(date +%Y%m%d_%H%M%S).sql

# 테이블별 백업
mysqldump -u root -p stock_data_cache daily_prices > daily_prices_backup.sql
mysqldump -u root -p community posts post_comments > community_backup.sql
```

## CI/CD 파이프라인

### Jenkins 파이프라인 구조
```
1. Checkout          - 소스코드 체크아웃
2. Debug Environment  - 환경변수 확인
3. Tests             - 프론트엔드/백엔드 병렬 테스트
4. JUnit Reports     - 테스트 결과 수집
5. Build & Push      - Docker 이미지 빌드 및 푸시
6. Deploy           - 프로덕션 배포
7. Integration Tests - 배포 후 통합 테스트
```

### 주요 환경변수 (Jenkins)
```bash
GHCR_OWNER=your-github-username
BACKEND_PROD_IMAGE=backtest-backend
FRONTEND_PROD_IMAGE=backtest-frontend
DEPLOY_HOST=your-production-host
DEPLOY_USER=deployment-user
DEPLOY_PATH_PROD=/opt/backtest
```

### 배포 스크립트
```bash
# 원격 배포 스크립트 (scripts/remote_deploy.sh)
#!/bin/bash
BACKEND_IMAGE=$1
FRONTEND_IMAGE=$2
DEPLOY_PATH=$3

cd $DEPLOY_PATH

# 이미지 풀
docker pull $BACKEND_IMAGE
docker pull $FRONTEND_IMAGE

# 서비스 재시작
docker compose down
BACKEND_IMAGE=$BACKEND_IMAGE FRONTEND_IMAGE=$FRONTEND_IMAGE docker compose up -d
```

### 로컬 CI 시뮬레이션
```bash
# 전체 CI 파이프라인 실행
./scripts/test-runner.sh ci

# 개별 단계 실행
./scripts/test-runner.sh lint      # 코드 품질 검사
./scripts/test-runner.sh unit      # 단위 테스트
./scripts/test-runner.sh integration  # 통합 테스트
./scripts/test-runner.sh e2e       # E2E 테스트
```

## 모니터링 및 헬스체크

### 헬스체크 엔드포인트
```bash
# 기본 헬스체크
curl http://localhost:8001/health

# 백테스트 특화 헬스체크
curl http://localhost:8001/api/v1/backtest/health
```

**응답 예시:**
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T10:00:00Z",
  "version": "1.0.0"
}
```

### 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너 확인
docker compose ps

# 컨테이너 로그 확인
docker compose logs -f backend
docker compose logs -f frontend

# 리소스 사용량 확인
docker stats
```

### 데이터베이스 모니터링
```sql
-- 연결 상태 확인
SHOW PROCESSLIST;

-- 테이블 크기 확인
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'stock_data_cache'
ORDER BY (data_length + index_length) DESC;

-- 최근 업데이트된 데이터 확인
SELECT 
    ticker,
    MAX(date) as last_date,
    COUNT(*) as total_records
FROM daily_prices dp
JOIN stocks s ON dp.stock_id = s.id
GROUP BY ticker
ORDER BY last_date DESC
LIMIT 10;
```

### 로그 관리
```bash
# 로그 레벨 설정 (환경변수)
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# 구조화된 로그 확인
docker compose logs backend | grep "ERROR"
docker compose logs backend | grep "WARNING"

# 로그 로테이션 (프로덕션)
docker compose logs --since="24h" backend > logs/backend_$(date +%Y%m%d).log
```

## 트러블슈팅

### 일반적인 문제들

#### 1. 데이터베이스 연결 실패
```bash
# 증상
ERROR: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")

# 해결 방법
1. DATABASE_URL 확인
2. MySQL 서비스 상태 확인: docker compose ps
3. 네트워크 연결 확인: docker network ls
4. 방화벽 설정 확인
```

#### 2. yfinance API 레이트 제한
```bash
# 증상  
429 Too Many Requests from yfinance

# 해결 방법
1. 요청 간격 조정 (백오프 전략)
2. 캐시된 데이터 우선 사용
3. 배치 처리로 요청 수 최소화
```

#### 3. 메모리 부족
```bash
# 증상
Container killed due to OOM (Out of Memory)

# 해결 방법
1. Docker 메모리 제한 증가
2. 백테스트 데이터 크기 제한
3. 가비지 컬렉션 최적화
```

#### 4. 프론트엔드 빌드 실패
```bash
# 증상
Error: Build failed with errors

# 해결 방법
1. npm 캐시 정리: npm cache clean --force
2. node_modules 재설치: rm -rf node_modules && npm ci
3. TypeScript 타입 오류 확인
```

### 성능 최적화

#### 백엔드 최적화
```python
# 데이터베이스 쿼리 최적화
# 인덱스 추가
CREATE INDEX idx_daily_prices_date ON daily_prices(date);
CREATE INDEX idx_stocks_ticker ON stocks(ticker);

# 커넥션 풀 설정
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True
}
```

#### 프론트엔드 최적화
```javascript
// 코드 스플리팅
const LazyComponent = lazy(() => import('./components/HeavyComponent'));

// 메모이제이션
const MemoizedChart = memo(Chart);
```

#### Docker 최적화
```dockerfile
# 멀티스테이지 빌드
FROM node:20-alpine as builder
# ... 빌드 단계

FROM nginx:alpine as production
# ... 운영 단계 (최소 이미지)
```

## 백업 및 복구

### 자동 백업 스크립트
```bash
#!/bin/bash
# scripts/backup.sh

BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 데이터베이스 백업
mysqldump -h mysql -u root -p"$MYSQL_ROOT_PASSWORD" \
  --all-databases \
  --single-transaction \
  --routines \
  --triggers > "$BACKUP_DIR/db_backup_$DATE.sql"

# 압축
gzip "$BACKUP_DIR/db_backup_$DATE.sql"

# 오래된 백업 삭제 (30일)
find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

### 복구 절차
```bash
# 1. 서비스 중지
docker compose down

# 2. 데이터베이스 복구
gunzip -c backup_20231201_120000.sql.gz | mysql -u root -p

# 3. 서비스 재시작
docker compose up -d

# 4. 헬스체크 확인
curl http://localhost:8001/health
```

### 스케줄링 (cron)
```bash
# 매일 새벽 2시 백업
0 2 * * * /opt/backtest/scripts/backup.sh >> /var/log/backup.log 2>&1

# 매주 일요일 로그 정리
0 3 * * 0 /opt/backtest/scripts/cleanup_logs.sh
```

### 모니터링 체크리스트
- [ ] 헬스체크 엔드포인트 응답 확인
- [ ] 데이터베이스 연결 상태 확인
- [ ] 디스크 사용량 모니터링
- [ ] 메모리 사용량 확인
- [ ] API 응답 시간 측정
- [ ] 에러 로그 분석
- [ ] 백업 파일 생성 확인

### 장애 대응 절차
1. **장애 감지**: 모니터링 알람 또는 사용자 신고
2. **즉시 조치**: 헬스체크 및 로그 확인
3. **원인 파악**: 에러 로그 분석 및 시스템 리소스 확인
4. **복구 작업**: 서비스 재시작 또는 롤백
5. **사후 조치**: 장애 원인 분석 및 재발 방지 계획 수립
