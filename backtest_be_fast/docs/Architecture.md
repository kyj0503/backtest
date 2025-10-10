# Architecture — FastAPI 백엔드

개요
- DDD에서 영감을 받은 계층 구조(프레젠테이션/애플리케이션/도메인/인프라)를 따른다.

디렉터리 맵
- `app/api/`
- `app/services/`
- `app/domains/`
- `app/repositories/`
- `app/events/`
- `app/factories/`
- `app/strategies/`
- `app/models/`
- `app/core/`
- `app/utils/`

핵심
- 이벤트: `app/events/`
- 팩토리 및 등록: `app/factories/`
- 설정: `app/core/config.py`

기여 가이드(요약)
1. 서비스 로직은 `app/services/`에 둔다.
2. 도메인 엔티티는 `app/domains/`에 추가한다(외부 의존성 금지).
3. 서비스나 팩토리 등록 관련 코드는 `app/factories/` 또는 관련 서비스 모듈에서 관리한다.
