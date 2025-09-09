# 커밋 메시지 규칙 (Conventional Commits)

일관된 변경 이력을 위해 Conventional Commits 규칙을 사용합니다.

## 기본 포맷
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

## 타입 목록
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

## 예시
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

## Breaking Change
하위 호환이 깨지는 변경은 `!` 또는 `BREAKING CHANGE:`를 명시합니다.
```
feat(api)!: 요청 스키마 필드명 변경 (stocks → portfolio)

BREAKING CHANGE: 기존 클라이언트는 요청 필드명을 업데이트해야 합니다.
```

## 링크/메타데이터
- 이슈 참조: `Refs #123`, `Closes #123`
- Co-authored-by: 여러 기여자 표기 가능

프로젝트의 실제 릴리즈 노트/체인지로그는 CI 파이프라인 또는 수작업으로 관리합니다.
