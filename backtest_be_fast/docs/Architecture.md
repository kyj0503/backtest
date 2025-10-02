# Architecture — FastAPI 백엔드

개요
- DDD에서 영감을 받은 계층 구조(프레젠테이션/애플리케이션/도메인/인프라)를 따른다.

디렉터리 맵
- `app/api/`, `app/services/`, `app/domains/`, `app/repositories/`, `app/cqrs/`, `app/events/`, `app/factories/`

핵심
- CQRS: `app/cqrs/`
- 이벤트: `app/events/`
- 설정: `app/core/config.py`

기여 가이드(요약)
1. 서비스 로직은 `app/services/`에 둔다.
2. 도메인 엔티티는 `app/domains/`에 추가한다(외부 의존성 금지).
3. 핸들러 등록은 `app/cqrs/service_manager.py`에서 수행한다.
