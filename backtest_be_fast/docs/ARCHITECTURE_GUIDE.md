# 04. 아키텍처 가이드 — FastAPI 백테스팅 서비스

## 개요
DDD(Domain-Driven Design)에서 영감을 받은 계층 구조를 구현합니다.

## 계층 구조
- **`api/`** (프레젠테이션): FastAPI 라우터, 엔드포인트
- **`services/`** (애플리케이션): 비즈니스 로직, 외부 서비스 호출
- **`domains/`** (도메인): 순수 비즈니스 엔티티, 값 객체 (IO 금지)
- **`repositories/`** (인프라): 데이터베이스, 외부 API 접근
- **`events/`** (통합): 비동기 이벤트 처리, 횡단 관심사

## 핵심 패턴

### CQRS (Command Query Responsibility Segregation)
- **위치**: `app/cqrs/`
- **등록**: `service_manager.py`에서 핸들러 와이어링
- **용도**: 명령(쓰기)과 쿼리(읽기) 분리

### 이벤트 시스템
- **위치**: `app/events/`
- **용도**: 메트릭 수집, 알림, 비동기 작업
- **장점**: 핵심 로직과 부가 기능 분리

### 의존성 주입
- **팩토리**: `app/factories/` - 서비스 생성 및 의존성 관리
- **설정**: `app/core/config.py` - 환경 기반 설정

## 데이터 저장소
- **MySQL**: 사용자, 커뮤니티, 백테스트 이력
- **yfinance 캐시**: 주식 데이터 임시 저장

## 모델 정의
- **요청/응답**: `app/models/` - Pydantic v2 기반
- **도메인**: `app/domains/` - 순수 Python 클래스

## 새 기능 추가 가이드

### 애플리케이션 레벨 기능
1. `services/`에 비즈니스 로직 작성
2. IO가 필요하면 비동기(`async`) 사용
3. `factories/`에서 의존성 주입 설정

### 도메인 엔티티
1. `domains/<bounded_context>/`에 배치
2. 외부 의존성 없는 순수 로직만 포함
3. 값 객체나 엔티티로 모델링

### CQRS 명령/쿼리
1. `cqrs/commands.py` 또는 `cqrs/queries.py`에 정의
2. 해당 핸들러를 `cqrs/` 하위에 구현
3. `service_manager.py`에 등록

### 이벤트 핸들러
1. `events/handlers/`에 핸들러 구현
2. 이벤트 시스템에 등록
3. 비동기 처리로 성능 영향 최소화
