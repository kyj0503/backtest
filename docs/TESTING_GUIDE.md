# 백테스트 프로젝트 테스트 가이드

이 문서는 백테스트 프로젝트의 완전한 테스트 전략, 아키텍처, 실행 방법을 다룹니다.

## 목차

1. [테스트 전략 개요](#테스트-전략-개요)
2. [테스트 아키텍처](#테스트-아키텍처)
3. [테스트 실행 방법](#테스트-실행-방법)
4. [테스트 유형별 설명](#테스트-유형별-설명)
5. [커버리지 및 품질 관리](#커버리지-및-품질-관리)
6. [CI/CD 통합](#cicd-통합)
7. [문제 해결](#문제-해결)

## 테스트 전략 개요

### 테스트 피라미드 구조
```
        E2E Tests (5-10%)
       핵심 사용자 시나리오
      
    Integration Tests (20-30%)
   서비스 간 연동, DB/API 통합
  
Unit Tests (60-70%)
빠른 피드백, 개별 컴포넌트 검증
```

### 핵심 원칙
- 빠른 피드백: 단위 테스트 중심의 빠른 개발 사이클
- 격리: 외부 의존성(DB, API) 최소화로 안정성 확보
- 재현성: Docker 기반 환경으로 일관된 테스트 실행
- 자동화: CI/CD 파이프라인 통합으로 지속적 품질 관리

### 품질 목표
- 커버리지: 70% 이상 유지
- 실행 시간: 단위 테스트 30초 이내, 전체 테스트 5분 이내
- 안정성: 98% 이상 테스트 성공률

## 테스트 아키텍처

### 백엔드 테스트 구조
```
backend/tests/
├── unit/                    # 단위 테스트 (개별 함수/클래스)
│   ├── test_backtest_service.py
│   ├── test_strategy_service.py
│   ├── test_data_fetcher.py
│   └── test_cash_assets.py
├── integration/             # 통합 테스트 (서비스 간 연동)
│   ├── test_api_endpoints.py
│   ├── test_backtest_flow.py
│   ├── test_auth_community.py
│   └── test_backtest_history_and_community_features.py
├── e2e/                     # E2E 테스트 (전체 시나리오)
│   └── test_complete_backtest.py
├── fixtures/                # 테스트 데이터 및 모킹
│   ├── mock_data.py
│   ├── expected_results.py
│   └── test_scenarios.json
└── conftest.py             # pytest 설정 및 공통 픽스처
```

### 프론트엔드 테스트 구조
```
frontend/src/test/
├── setup.ts               # Vitest 초기화
├── components/             # 컴포넌트 테스트
├── hooks/                  # 커스텀 훅 테스트
├── services/               # API 서비스 테스트
└── utils/                  # 유틸리티 함수 테스트
```

### 테스트 환경 설정

#### pytest 설정 (backend/pytest.ini)
```ini
[tool:pytest]
minversion = 6.0
addopts = -ra --tb=short -v --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=70
testpaths = tests/
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (moderate speed, service interactions)
    e2e: End-to-end tests (slow, full system)
    slow: Slow tests (may take more than 10 seconds)
    asyncio: Async tests
```

#### Docker 테스트 환경
- 격리된 데이터베이스: MySQL 8.0 + Redis (compose/compose.test.yml)
- 네트워크 분리: 테스트 전용 Docker 네트워크
- 자동 정리: 테스트 완료 후 자동 컨테이너 정리

## 테스트 실행 방법

### 간편 실행 (권장: 스크립트 사용)
```bash
# 기본 단위 테스트 (가장 빠름)
./scripts/test-runner.sh unit

# 특정 테스트 유형
./scripts/test-runner.sh unit          # 단위 테스트만
./scripts/test-runner.sh integration   # 통합 테스트 (DB 포함)
./scripts/test-runner.sh e2e           # E2E 테스트
./scripts/test-runner.sh all           # 모든 테스트

# 품질 관리
./scripts/test-runner.sh coverage      # 커버리지 리포트 생성
./scripts/test-runner.sh lint          # 코드 품질 검사

# CI 파이프라인 시뮬레이션
./scripts/test-runner.sh ci            # 전체 CI 파이프라인 실행
```

### test-runner.sh 스크립트 직접 사용
```bash
# 기본 사용법
./scripts/test-runner.sh [command]

# 사용 가능한 명령어 (예시)
unit        # 단위 테스트 (빠른 피드백)
integration # 통합 테스트 (데이터베이스 포함)
e2e         # E2E 테스트 (전체 시스템)
frontend    # 프론트엔드 테스트
all         # 모든 테스트 실행
coverage    # 커버리지 분석
lint        # 코드 품질 검사
ci          # CI 파이프라인 시뮬레이션
```

### Docker 직접 사용
```bash
# 백엔드 단위 테스트
docker build -t backtest-backend-test backend/
docker run --rm backtest-backend-test python -m pytest tests/unit/ -v

# 통합 테스트 (데이터베이스 필요)
docker-compose -f compose/compose.test.yml up -d
docker run --rm --network compose_test_network \
  -e DATABASE_URL="mysql+pymysql://test_user:test_password@mysql-test:3306/stock_data_cache" \
  backtest-backend-test python -m pytest tests/integration/ -v
```

## 테스트 유형별 설명

### 1. 단위 테스트 (Unit Tests)
**목적**: 개별 함수, 클래스, 모듈의 동작 검증

**특징**:
- 외부 의존성 없음 (모킹 사용)
- 실행 시간 < 1초
- 높은 커버리지 목표 (80%+)

**예시 테스트**:
- `test_backtest_service.py`: 백테스트 로직 검증
- `test_strategy_service.py`: 전략 실행 로직
- `test_data_fetcher.py`: 데이터 수집 및 변환
- `test_cash_assets.py`: 현금 자산 계산

**실행 방법**:
```bash
make test-unit
# 또는
./scripts/test-runner.sh unit
```

### 2. 통합 테스트 (Integration Tests)
**목적**: 서비스 간 연동, 데이터베이스 통합 검증

**특징**:
- 실제 데이터베이스 연결
- API 엔드포인트 검증
- 비즈니스 플로우 검증

**예시 테스트**:
- `test_api_endpoints.py`: REST API 동작 검증
- `test_backtest_flow.py`: 백테스트 전체 플로우
- `test_auth_community.py`: 인증 및 커뮤니티 기능

**실행 방법**:
```bash
make test-integration
# 또는
./scripts/test-runner.sh integration
```

### 3. E2E 테스트 (End-to-End Tests)
**목적**: 사용자 관점의 전체 시스템 검증

**특징**:
- 실제 사용자 시나리오 재현
- 프론트엔드 + 백엔드 통합
- 가장 느리지만 높은 신뢰성

**예시 테스트**:
- `test_complete_backtest.py`: 완전한 백테스트 시나리오

**실행 방법**:
```bash
make test-e2e
# 또는
./scripts/test-runner.sh e2e
```

### 4. 프론트엔드 테스트
**도구**: Vitest + jsdom

**테스트 유형**:
- 컴포넌트 렌더링 테스트
- 사용자 상호작용 테스트
- API 서비스 모킹 테스트

**실행 방법**:
```bash
./scripts/test-runner.sh frontend
```

## 커버리지 및 품질 관리

### 현재 커버리지 현황 (2024-12-19 기준)
```
전체 커버리지: 27% (목표: 70%)

모듈별 상세:
models/responses.py: 100%
services/strategy_service.py: 92%
models/requests.py: 81%
services/backtest_service.py: 69%
factories/service_factory.py: 71%
api/v1/endpoints/*: 15-86%
cqrs/*: 0%
domains/*: 0%
events/*: 0%
```

### 커버리지 개선 우선순위
1. 높은 우선순위: API 엔드포인트 (15-86% → 80%+)
2. 중간 우선순위: CQRS 핸들러 (0% → 70%+)
3. 낮은 우선순위: 도메인 레이어 (0% → 50%+)

### 품질 체크리스트
- [ ] 모든 새 코드는 테스트 포함
- [ ] 커버리지 70% 이상 유지
- [ ] CI 파이프라인 통과
- [ ] 코드 리뷰 승인

## CI/CD 통합

### GitHub Actions / Jenkins 파이프라인
```yaml
# 예시 파이프라인 단계
1. 코드 품질 검사 (lint)
2. 단위 테스트 실행
3. 통합 테스트 실행
4. 빌드 및 이미지 생성
5. E2E 테스트 실행
6. 커버리지 리포트 생성
7. 배포 (조건부)
```

### 로컬 CI 시뮬레이션
```bash
# 전체 CI 파이프라인 실행 (스크립트 기반)
./scripts/test-runner.sh ci

# 또는 개별 단계 실행
./scripts/test-runner.sh lint
./scripts/test-runner.sh unit
./scripts/test-runner.sh integration
# 개발환경 빌드는 docker compose를 사용합니다
docker compose -f compose.yml -f compose/compose.dev.yml build
./scripts/test-runner.sh e2e
```

## 문제 해결

### 일반적인 문제들

#### 1. MySQL 연결 실패
**문제**: `pymysql.err.OperationalError: (2003, "Can't connect to MySQL server")`

**해결책**:
```bash
# 테스트 데이터베이스가 실행 중인지 확인
docker-compose -f compose/compose.test.yml ps

# 네트워크 연결 확인
docker network ls | grep test

# 컨테이너 재시작
docker-compose -f compose/compose.test.yml down -v
docker-compose -f compose/compose.test.yml up -d
```

#### 2. 커버리지 임계값 실패
**문제**: `Coverage failure: total of XX is less than fail-under=70`

**해결책**:
1. 누락된 테스트 식별: `./scripts/test-runner.sh coverage` 실행 후 `backend/htmlcov/index.html` 확인
2. 우선순위 모듈부터 테스트 추가
3. 임시로 임계값 조정 (권장하지 않음)

#### 3. Docker 빌드 실패
**문제**: 의존성 설치 또는 빌드 오류

**해결책**:
```bash
# Docker 캐시 정리
docker system prune -f

# 새로 빌드
docker build --no-cache -t backtest-backend-test backend/
```

#### 4. 테스트 실행 시간 초과
**문제**: 테스트가 너무 오래 걸림

**해결책**:
- 단위 테스트에 `@pytest.mark.slow` 마커 추가
- 병렬 실행: `pytest -n auto`
- 불필요한 설정 제거

### 성능 최적화 팁

1. Docker 레이어 캐싱 활용
   - requirements.txt 변경 없으면 의존성 설치 스킵
   - 코드 변경만으로는 전체 재빌드 방지

2. 테스트 데이터 최적화
   - 최소한의 테스트 데이터 사용
   - 픽스처 재사용 최대화

3. 병렬 실행
   - 단위 테스트: `pytest -n auto`
   - 통합 테스트: 데이터베이스 격리 필요시 주의

## 테스트 현황 및 메트릭

### 실행 시간 벤치마크
- 단위 테스트: ~8초 (42개 테스트)
- 통합 테스트: ~8초 (24개 테스트)
- E2E 테스트: ~10초 (6개 테스트)
- 전체 CI 파이프라인: ~3분 (빌드 포함)

### 성공률 지표
- 단위 테스트: 98% (42/43 통과, 1개 스킵)
- 통합 테스트: 96% (23/24 통과, 1개 DB 이슈)
- E2E 테스트: 100% (6/6 통과)

## 향후 계획

### 단기 목표 (1-2주)
- [ ] MySQL 연결 문제 완전 해결
- [ ] 커버리지 70% 달성
- [ ] CI 파이프라인 안정화

### 중기 목표 (1-2개월)
- [ ] Contract 테스트 도입 (Pact)
- [ ] 성능 테스트 추가 (Locust)
- [ ] 자동화된 E2E 테스트 확장

### 장기 목표 (3-6개월)
- [ ] Mutation 테스트 도입
- [ ] 시각적 회귀 테스트
- [ ] 부하 테스트 및 스트레스 테스트

---

## 기여 가이드

새로운 테스트를 추가할 때:
1. 적절한 테스트 유형 선택 (unit/integration/e2e)
2. 명확한 테스트 이름 작성
3. 필요한 마커 추가 (`@pytest.mark.unit` 등)
4. 문서 업데이트

문서 업데이트: 2024-12-19  
다음 리뷰: 커버리지 70% 달성 후
