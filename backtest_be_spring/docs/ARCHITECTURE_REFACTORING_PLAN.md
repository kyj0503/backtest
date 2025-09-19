# Spring Backend Domain-Oriented Refactoring Plan

## 목표
- **명확한 계층 분리**: `presentation → application → domain → infrastructure` 흐름을 유지하면서, 역방향 의존 제거.
- **도메인 주도 설계 강화**: 도메인 상태 변경과 비즈니스 규칙을 엔티티/도메인 서비스가 책임지도록 이동.
- **애플리케이션 서비스 경량화**: 트랜잭션 orchestration, 도메인 호출, DTO 변환만 담당.
- **인프라 계층 확립**: JPA/Redis/WebSocket 구현체를 infrastructure로 이동하고 인터페이스 기반 의존으로 교체.

## 전반 구조 개편
```
com.webproject.backtest_be_spring
├── application
│   ├── community
│   │   ├── command / dto / service
│   ├── chat
│   ├── admin
│   └── auth (기존 유지)
├── domain
│   ├── community
│   │   ├── model (엔티티/값객체)
│   │   ├── service (도메인 서비스)
│   │   └── repository (도메인 인터페이스)
│   ├── chat
│   ├── admin
│   └── user (기존 유지)
├── infrastructure
│   ├── persistence
│   │   ├── community (JPA 구현체 + Spring Data adapter)
│   │   ├── chat
│   │   └── admin
│   ├── messaging (Redis pub/sub, WebSocket broker 설정)
│   └── config (DB, Redis, WebSocket 등 공용 설정)
└── presentation
    ├── api (REST 컨트롤러)
    └── websocket (STOMP endpoint)
```

## 단계별 리팩터링 로드맵

### 1. 계층 분리 및 패키지 이동
- 도메인 엔티티/enum → `domain.*.model`
- JPA Repository 인터페이스 → `domain.*.repository` (interface만 정의)
- Spring Data 구현체 → `infrastructure.persistence.*` (e.g. `JpaPostRepository`)
- Redis/WebSocket 컴포넌트 → `infrastructure.messaging`
- REST/WebSocket 엔드포인트 → `presentation.api` / `presentation.websocket`

### 2. 도메인 로직 재구성
- 파생 컬럼(view/like/comment count) 조정 로직을 `domain.community.service`의 도메인 서비스로 집중시키고, 엔티티 메서드는 순수 상태 변경만 담당.
- 댓글 트리 조회는 커스텀 리포지토리 쿼리(CTE 혹은 fetch join)로 교체하여 N+1 제거.
- 채팅방 입장/퇴장, 공지 생성 등 핵심 규칙을 도메인 서비스로 이동 후 테스트 작성.

### 3. 애플리케이션 서비스 정리
- Command/Query 객체를 통해 입력 정규화.
- 트랜잭션 경계(`@Transactional`)는 애플리케이션 서비스 최상단에서만 유지.
- DTO 변환은 Mapper 또는 static factory로 위임.

### 4. 인프라 계층 확립
- Spring Data JPA repository 구현 클래스가 도메인 repository 인터페이스를 구현하도록 adapter 패턴 적용.
- Redis Pub/Sub + STOMP 설정을 infrastructure로 이동, presentation 계층은 메시지 DTO만 다루도록 한다.
- configuration class들도 역할에 따라 `infrastructure.config`로 이동 후 빈 주입 경로 점검.

### 5. 보완 작업
- Swagger/OpenAPI 경로 업데이트 (패키지 이동에 따른 scan basePackage 조정 필요 시 반영).
- Security 설정의 URL 조정(새로운 엔드포인트 경로 반영).
- 통합/단위 테스트 추가: 도메인 서비스, 애플리케이션 서비스, REST/WebSocket API 기본 시나리오.

## 작업 분할 제안
1. **Phase A**: 패키지 이동 + 도메인/인프라/프레젠테이션 skeleton 정리.
2. **Phase B**: 커뮤니티 도메인 리팩터링 + 관련 REST API 정비.
3. **Phase C**: 채팅 도메인/메시징 리팩터링.
4. **Phase D**: 관리자 기능 및 통계/공지/신고 흐름 정리.
5. **Phase E**: 통합 테스트 및 문서 보강.

> 각 Phase 완료 시점에 컴파일/테스트 확인 및 문서(예: README, Swagger Docs) 업데이트를 포함합니다.

