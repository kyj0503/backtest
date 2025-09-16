# 기여 가이드 (Contributing)

프로젝트에 기여해 주셔서 감사합니다. 안정적인 빌드와 일관된 문서/코드 품질을 위해 아래 규칙을 따라 주세요.

## 개발 환경
- 표준 개발·테스트는 Docker/Compose 기반입니다(개발: compose.dev.yml 병합).
- 백엔드 테스트는 pytest, 프론트는 Vitest를 사용합니다.
참고: 컨테이너 내부 명령 실행으로 일관성을 유지합니다.

## 브랜치/PR 정책
- 브랜치 이름: `feature/…`, `fix/…`, `docs/…`, `chore/…`
- PR 제목: Conventional Commits 요약 규칙 권장
- PR 설명: 문제/목표/변경사항/테스트 범위 요약
- 작은 단위의 PR을 선호합니다. 커밋은 논리적으로 나누고, 불필요한 리포맷만의 커밋은 피해주세요.


## 커밋 메시지 규칙 (Conventional Commits)

일관된 변경 이력을 위해 Conventional Commits 규칙을 사용합니다.

### 기본 포맷
```
<type>(<scope>): <subject>

<body>

<footer>
```
- `type`: 변경 유형
- `scope`: 영향 범위(선택, 예: api, backend, frontend, docs, tests)
- `subject`: 간결한 한 줄 요약 (명령형, 마침표 X)
- `body`: 배경/동기/변경 상세 (선택)
- `footer`: 관련 이슈/브레이킹 체인지 (선택)

### 타입 목록
- `feat`: 사용자 가치가 있는 신규 기능
- `fix`: 버그 수정
- `docs`: 문서 수정/추가
- `refactor`: 기능 변화 없는 리팩터링
- `perf`: 성능 개선
- `test`: 테스트 추가/개선
- `build`: 빌드 시스템/종속성 변경
- `ci`: CI 설정/스크립트 변경
- `chore`: 잡무(소스/테스트/빌드에 영향 없는 변경)
- `revert`: 이전 커밋 되돌리기

### 예시
```
feat(api): 포트폴리오 최적화 엔드포인트 추가

- mean-variance 기반 가중치 계산 추가
- 백테스트 결과에 optimized_weights 포함

Closes #123
```
```
fix(backend): 잘못된 500 → 422 상태코드 수정

유효하지 않은 티커 입력 시 422를 반환하도록 수정
```
```
docs(readme): 개발 빠른 시작에 githooks 설정 추가
```
```
refactor(frontend): 커스텀 훅으로 폼 로직 분리

- useBacktestForm, useFormValidation 도입
```
```
perf(backtest): 지표 계산 벡터화로 35% 단축
```

### Breaking Change
하위 호환이 깨지는 변경은 `!` 또는 `BREAKING CHANGE:`를 명시합니다.
```
feat(api)!: 요청 스키마 필드명 변경 (stocks → portfolio)

BREAKING CHANGE: 기존 클라이언트는 요청 필드명을 업데이트해야 합니다.
```

### 링크/메타데이터
- 이슈 참조: `Refs #123`, `Closes #123`
- Co-authored-by: 여러 기여자 표기 가능

프로젝트의 실제 릴리즈 노트/체인지로그는 CI 파이프라인 또는 수작업으로 관리합니다.

## 코드/문서 스타일
- Python: PEP8과 Black/isort, 타입 힌트 권장.
- TypeScript/React: 명시적 타입, 단일 책임, 훅 분리 원칙.
- 문서: `docs/` 하위에 추가하고 `docs/README.md`에 링크합니다.

## 테스트
- 백엔드: pytest. 단위 → 통합 → e2e 우선순위로 작성합니다.
- 프론트엔드: Vitest + @testing-library. 스냅샷 남용을 지양합니다.
- 외부 의존성(yfinance, DB)은 모킹을 우선합니다. 자세한 내용은 `docs/TESTING_GUIDE.md` 참고.

## 테스트 실행
- 백엔드: `./scripts/test-runner.sh unit`, `integration`, `e2e`
- 프론트엔드: `./scripts/test-runner.sh frontend`
- 전체 품질 확인: `./scripts/test-runner.sh all`

## 이슈/디스커션
- 버그: 재현 단계, 기대 동작/실제 동작, 로그/스크린샷을 포함해 주세요.
- 기능: 배경/문제, 제안 내용, 대안, 영향 범위를 포함해 주세요.
- 문서: 링크 깨짐/오탈자/불일치 발견 시 자유롭게 PR 환영합니다.

감사합니다!
