# 04. Architecture — FastAPI 백엔드

개요
- DDD에서 영감을 받은 계층 구조(프레젠테이션, 애플리케이션, 도메인, 인프라)를 따릅니다.

디렉터리 맵
- `api/`, `services/`, `domains/`, `repositories/`, `cqrs/`, `events/`, `factories/`

핵심 패턴
- CQRS: `app/cqrs/`
- 이벤트: `app/events/`
- 설정: `app/core/config.py`

기여 가이드 (간단)
1. 서비스 로직은 `app/services/`에 작성
2. 도메인 엔티티는 `app/domains/`에 추가(외부 의존성 금지)
3. 핸들러 등록은 `cqrs/service_manager.py`에서 수행
