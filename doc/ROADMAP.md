# 로드맵 및 향후 계획

백테스팅 시스템의 향후 개발 계획과 목표입니다.

## 현재 상태

### 완료된 주요 기능
- **진짜 현금 자산 처리**: asset_type 필드로 현금('cash')과 주식('stock') 구분
- **Pydantic V2 완전 마이그레이션**: 모든 deprecated 경고 제거
- **네이버 뉴스 API**: 70+ 종목 지원, 날짜별 필터링, 자동 콘텐츠 정제
- **완전 오프라인 모킹 시스템**: CI/CD 안정성 극대화

### Jenkins CI/CD 파이프라인 상태
- **Frontend Tests**: 23/23 통과 (100%)
- **Backend Tests**: 65/68 통과 (95.3% + 3개 정상 스킵)
- **빌드 및 배포**: 모든 단계 성공
- **크로스 플랫폼 호환성**: Windows CRLF → Unix LF 완전 해결

## 향후 로드맵

### 단기 목표 (1-3개월)
- [ ] 회원 가입/로그인 시스템
- [ ] 포트폴리오 저장 기능
- [ ] 백테스트 결과 개선 (월별 분석 등)
- [ ] 모바일 반응형 UI 개선

### 중기 목표 (3-6개월)
- [ ] 실시간 데이터 업데이트 (WebSocket)
- [ ] AI 기반 포트폴리오 분석 (OpenAI API)
- [ ] 커뮤니티 기능 (수익률 공유)
- [ ] 고급 차트 분석 도구

### 장기 목표 (6-12개월)
- [ ] 마이크로서비스 아키텍처 전환
- [ ] 클라우드 배포 (AWS/GCP)
- [ ] 머신러닝 기반 전략 추천
- [ ] 다국어 지원 및 글로벌 확장

## To-Do 우선순위

### 1. High (비즈니스 핵심 기능)
- [x] 진짜 현금 자산 처리: asset_type 필드로 현금과 주식 구분, 무위험 자산으로 0% 수익률 보장
- [ ] 백테스트 결과 개선: 월별/연도별 수익률 분석, 베타 계수, 최대 연속 손실 기간 등 추가 통계 제공
- [ ] 회원 가입 기능: 사용자 관리 시스템 구축
- [ ] 내 포트폴리오 저장 기능: 사용자별 포트폴리오 관리

### 2. Medium (사용자 경험 개선)
- [ ] 폼 상태 관리 개선: `UnifiedBacktestForm.tsx`의 복잡한 상태를 useReducer로 리팩토링
- [ ] TypeScript 타입 안정성: 이벤트 핸들러 타입 명시로 any 타입 제거
- [ ] 테스트 커버리지 향상: 단위/통합/E2E 테스트 강화

### 3. Low (고급 기능 및 확장)
- [ ] OpenAI API 포트폴리오 적합성 분석: AI 기반 투자 성향 분석
- [ ] 커뮤니티 기능: 수익률 공유 및 랭킹 시스템
- [ ] 주식 티커 자동 완성: 자연어 → 티커 자동 변환

## 참고 자료

### 공식 문서
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **TypeScript**: https://www.typescriptlang.org/
- **Docker**: https://docs.docker.com/

### 프로젝트 관련
- **backtesting.py**: https://kernc.github.io/backtesting.py/
- **yfinance**: https://pypi.org/project/yfinance/
- **React Bootstrap**: https://react-bootstrap.github.io/
- **Recharts**: https://recharts.org/

### 커뮤니티
- **GitHub Discussions**: 프로젝트 관련 질문 및 토론
- **Discord**: 실시간 개발자 소통 (향후 개설 예정)
- **Wiki**: 상세한 개발 가이드 및 팁
