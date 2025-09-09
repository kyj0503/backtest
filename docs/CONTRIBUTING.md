# 기여 가이드 (Contributing)

프로젝트에 기여해 주셔서 감사합니다. 안정적인 빌드와 일관된 문서/코드 품질을 위해 아래 규칙을 따라 주세요.

## 개발 환경
- 기본 표준은 Docker/Compose입니다.
- 로컬 실행 시에도 Docker를 권장합니다.

```bash
# 개발 환경 실행 (루트에서)
docker compose -f compose.yml -f compose/compose.dev.yml up --build

# 백그라운드 실행/종료
docker compose -f compose.yml -f compose/compose.dev.yml up -d
docker compose -f compose.yml -f compose/compose.dev.yml down

# 백엔드 테스트 (컨테이너 내부)
docker compose exec backend pytest tests/ -v

# 프론트엔드 테스트 (컨테이너 내부)
docker compose exec frontend npm test
```

참고: 백엔드 패키지는 uv로 설치/관리하며, Dockerfile에서 이미 적용합니다. 로컬 수동 설치가 필요하면 `backend/` 디렉터리에서 실행하세요.

```bash
cd backend
uv pip install --system -r requirements.txt
```

## 브랜치/PR 정책
- 브랜치 이름: `feature/…`, `fix/…`, `docs/…`, `chore/…`
- PR 제목: [Conventional Commits](COMMIT_CONVENTION.md) 요약 규칙 권장
- PR 설명: 문제/목표/변경사항/테스트 범위 요약
- 작은 단위의 PR을 선호합니다. 커밋은 논리적으로 나누고, 불필요한 리포맷만의 커밋은 피해주세요.

## 커밋 메시지
- [Conventional Commits](COMMIT_CONVENTION.md) 규칙 사용을 권장합니다.
- 예시: `feat(api): 포트폴리오 최적화 엔드포인트 추가`
- 주요 타입: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `ci`, `build`, `perf`, `revert`

자세한 포맷과 예시는 COMMIT_CONVENTION.md를 참고하세요.

## 코드/문서 스타일
- Python: PEP8 권장. 타입 힌트를 사용합니다.
- TypeScript/React: 명시적 타입, 컴포넌트 단일 책임, 커스텀 훅 분리 원칙을 따릅니다.
- 문서: `docs/` 디렉터리에 주제별 Markdown 파일로 추가하고, `docs/README.md`에서 링크하세요.

## 테스트
- 백엔드: pytest. 단위 → 통합 → e2e 우선순위로 작성합니다.
- 프론트엔드: Vitest + @testing-library. 스냅샷 남용을 지양합니다.
- 외부 의존성(yfinance, DB)은 모킹을 우선합니다. 자세한 내용은 `docs/TEST_ARCHITECTURE.md` 참고.

## Git Hooks (선택적 권장)
저장소에는 사전 검증용 pre-commit 훅이 포함되어 있습니다.

```bash
# 루트에서 Git hooks 경로 설정 (1회)
git config core.hooksPath .githooks

# 훅이 실행하는 스크립트
.githooks/pre-commit -> scripts/verify-before-commit.sh
```

- 훅은 백/프론트 Docker 빌드+테스트, 간단 헬스체크를 수행합니다.
- 긴 빌드 시간이 부담되는 경우 `--no-verify`로 우회할 수 있으나, PR 전에는 반드시 통과시켜 주세요.

## 이슈/디스커션
- 버그: 재현 단계, 기대 동작/실제 동작, 로그/스크린샷을 포함해 주세요.
- 기능: 배경/문제, 제안 내용, 대안, 영향 범위를 포함해 주세요.
- 문서: 링크 깨짐/오탈자/불일치 발견 시 자유롭게 PR 환영합니다.

감사합니다!

