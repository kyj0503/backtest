# 백엔드 기술 문서

이 디렉토리에는 백엔드 시스템 아키텍처, 핵심 로직, 문제 해결 가이드에 대한 기술 문서가 포함되어 있습니다.

## 디렉토리 구조

- analysis/ - 코드 품질 분석 및 결과
- architecture/ - 시스템 아키텍처 및 설계 문서
- performance/ - 성능 최적화 문서
- refactoring/ - 코드 리팩터링 문서
- testing/ - 테스트 전략 및 가이드
- troubleshooting/ - 일반적인 문제 및 해결 방법

## 아키텍처

- [백테스트 로직 아키텍처](./architecture/backtest_logic.md)
  - backtesting.py 라이브러리의 역할
  - 커스텀 구현 경계
  - 통화 변환 및 동적 전략 생성

- [날짜 계산 아키텍처 (N번째 특정 요일)](./architecture/date_calculation.md)
  - DCA 및 리밸런싱을 위한 N번째 요일 계산 로직
  - 예외 상황 처리 (5번째 주가 없는 달)

- [전략 구현 가이드](./architecture/strategies.md)
  - 매매 전략 (SMA, RSI, MACD 등)
  - 포지션 관리 패턴

## 성능

- [최적화 요약](./performance/optimization-summary.md)
  - N+1 쿼리 패턴 최적화 (10배 속도 향상)
  - 병렬 데이터 로딩 개선
  - 코드 품질 지표 개선 전후

## 리팩터링

- [포트폴리오 함수 분석](./refactoring/portfolio-function-analysis.md)
  - calculate_dca_portfolio_returns() 구조 분석
  - 복잡도 지표 및 분해 전략

- [함수 추출 명세](./refactoring/function-extraction-specs.md)
  - 추출된 8개 헬퍼 함수의 상세 명세
  - 입출력 계약 및 책임

- [함수 구조 다이어그램](./refactoring/function-structure-diagram.md)
  - 함수 관계의 시각적 표현
  - 데이터 흐름 다이어그램

## 분석

- [백엔드 분석 인덱스](./analysis/backend-analysis-index.md)
  - 모든 분석 문서 개요
  - 특정 결과로의 빠른 이동

- [코드 중복 보고서](./analysis/code-duplication-index.md)
  - 중복 함수 위치 및 통합 계획
  - 데이터 로딩 패턴 분석

- [로깅 누락 분석](./analysis/logging-gaps-detailed.md)
  - 누락된 로깅 지점 식별
  - 운영 가시성 개선

- [에러 형식 분석](./analysis/error-format-analysis.md)
  - 에러 메시지 일관성 문제
  - 표준화 권장사항

## 문제 해결

- [비동기/동기 경계 문제 (레이스 컨디션)](./troubleshooting/race_condition.md)
  - 첫 실행 시 백테스트 손상 원인
  - 올바른 asyncio.to_thread() 사용법

- [DB 트랜잭션 격리 문제](./troubleshooting/transaction_isolation.md)
  - 저장 후 쿼리 실패 원인
  - 트랜잭션 스냅샷 갱신 패턴

- [성능 최적화 가이드](./troubleshooting/performance.md)
  - 성능 병목 지점 분석
  - 적용된 최적화 전략
  - 향후 개선 로드맵

## 테스팅

- [테스트 문서](./testing/README.md)
  - 테스트 전략 및 실행 방법
  - 픽스처 및 테스트 데이터 관리

## 빠른 참조

빠른 조회를 위한 문서:
- 성능 지표: performance/optimization-summary.md
- 일반 에러: analysis/error-format-analysis.md
- 코드 중복: analysis/code-duplication-reference.txt
- 함수 추출: refactoring/function-extraction-guide.txt
