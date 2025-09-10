# 문서 가이드

백테스팅 시스템의 모든 문서는 이 폴더에서 관리됩니다. 필요한 문서를 쉽게 찾을 수 있도록 주제별로 정리되어 있습니다.

## 핵심 가이드

### 개발자용
- **[개발 가이드](DEVELOPMENT_GUIDE.md)** - 개발 환경 설정, 백엔드/프론트엔드 개발 방법
- **[테스트 가이드](TESTING_GUIDE.md)** - 테스트 전략, 실행 방법, 커버리지 관리
- **[아키텍처 가이드](ARCHITECTURE_GUIDE.md)** - 시스템 설계, DDD 패턴, 컴포넌트 구조

### 운영자용
- **[API 가이드](API_GUIDE.md)** - API 엔드포인트, 요청/응답 예시, 인증 방법
- **[운영 가이드](OPERATIONS_GUIDE.md)** - 배포, 모니터링, 트러블슈팅, CI/CD

## 문서 활용법

### 처음 시작하는 경우
1. 프로젝트 개요: 루트 `README.md` 참고
2. 개발 환경 구성: `DEVELOPMENT_GUIDE.md` → 환경 설정 섹션
3. 첫 실행: `DEVELOPMENT_GUIDE.md` → 빠른 시작 섹션

### 개발 중인 경우
- 새 기능 개발: `DEVELOPMENT_GUIDE.md` + `ARCHITECTURE_GUIDE.md`
- API 연동: `API_GUIDE.md`
- 테스트 작성: `TESTING_GUIDE.md`
- 배포 준비: `OPERATIONS_GUIDE.md`

### 문제 해결이 필요한 경우
- 개발 환경 문제: `DEVELOPMENT_GUIDE.md` → 트러블슈팅 섹션
- 운영 환경 문제: `OPERATIONS_GUIDE.md` → 트러블슈팅 섹션
- API 오류: `API_GUIDE.md` → 오류 처리 섹션

## 문서 유지보수

이 문서들은 코드 변경사항에 맞춰 지속적으로 업데이트됩니다. 문서 개선 제안이 있으시면 이슈나 PR을 통해 알려주세요.
