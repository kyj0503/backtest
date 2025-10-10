# Architecture — FastAPI 백엔드

개요
- 단순하고 명확한 계층 구조를 따른다 (API → Services → Repositories)

디렉터리 맵
- `app/api/` - FastAPI 라우터 및 엔드포인트
- `app/services/` - 비즈니스 로직
- `app/domains/` - 도메인 모델
- `app/repositories/` - 데이터 액세스 계층
- `app/strategies/` - 백테스팅 전략 구현
- `app/models/` - Pydantic 요청/응답 모델
- `app/core/` - 설정 및 예외 처리
- `app/utils/` - 유틸리티 함수
- `app/strategy_registry.py` - 전략 레지스트리 (간소화)

핵심
- 전략 관리: `app/strategy_registry.py` - 전략 등록 및 검증
- 설정: `app/core/config.py`
- 서비스: `app/services/backtest_service.py` - 메인 백테스트 서비스

기여 가이드(요약)
1. 서비스 로직은 `app/services/`에 둔다.
2. 도메인 엔티티는 `app/domains/`에 추가한다(외부 의존성 금지).
3. 새로운 전략은 `app/strategies/`에 추가하고 `strategy_registry.py`에 등록한다.
