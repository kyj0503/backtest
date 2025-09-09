# Domain-Driven Design 아키텍처 가이드

상태: 부분 적용 중. 실제 비즈니스 로직은 현재 `backend/app/services/*`가 중심이며, `backend/app/domains/*`는 점진 도입·확장 단계입니다. `backend/app/cqrs/*`와 `backend/app/events/*`는 패턴 기반의 구조를 마련해 두었고, 선택 기능에서 사용합니다.

## 현재 구조 개요
- Backtest: 백테스트 실행과 차트 데이터 생성은 서비스 계층이 담당합니다. 핵심 파일은 `services/backtest_service.py`, `services/backtest/backtest_engine.py`입니다.
- Portfolio: 포트폴리오 백테스트와 리밸런싱 옵션은 `services/portfolio_service.py`가 제공하며, 현금 자산 처리와 DCA 시뮬레이션을 포함합니다.
- Data: `services/yfinance_db.py`가 DB 캐시 우선 정책을 담당하고, 누락 구간은 yfinance로 보강합니다.
- API: `app/api/v1/endpoints/*`에 백테스트, 전략, 최적화, 뉴스, 인증, 커뮤니티, 채팅(WebSocket) 엔드포인트가 구성되어 있습니다.

## 도메인 방향성 (점진 도입)
- Backtest Domain: 결과/지표/기간 등 값 객체와 엔티티 정의를 확대하고, 서비스 레이어에서 계산을 위임하도록 전환합니다.
- Portfolio Domain: 가중치/제약/상관·군집 분석을 도메인 서비스로 승격하고, 리밸런싱/턴오버 정책을 명확히 모델링합니다.
- Data Domain: 데이터 무결성(룩어헤드 방지, 결측 처리) 규칙을 값 객체/도메인 서비스에 내재화합니다.

## 구현 현황 요약
- 서비스 레이어 중심 구현 완료: 단일 종목 백테스트, 차트 데이터, 포트폴리오 백테스트, 환율 조회.
- 데이터 소스 정책: DB 캐시 우선, 부재 시 yfinance 조회 후 upsert.
- 이벤트/CQRS: 이벤트 발행·구독, 쿼리·커맨드 분리는 선택 기능에서 사용하며 점진 확대 예정.

## 향후 계획
- DDD 전술 패턴 내재화: 값 객체 불변성, 엔티티 식별/수명주기, 도메인 서비스 무상태 원칙 적용 강화.
- 최적화 도메인 확장: HRP/HERC, CVaR 등 고급 포트폴리오 최적화 기능을 별도 도메인 서비스로 격리.
- 테스트 정렬: 도메인 단위 테스트를 보강하고, 서비스→도메인 전환 구간에 계약(Contract) 성격 테스트 도입.
