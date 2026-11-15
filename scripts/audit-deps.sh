#!/usr/bin/env sh
# 의존성 취약점 감사 (CI 배포 전 검사)
#
# Go 모듈과 표준 라이브러리에 대해 govulncheck를 돌린다. govulncheck는 코드에서 실제로 호출되는
# 취약 함수만 보고하므로 예외 목록을 두지 않는다. 보고가 나오면 모듈 또는 Go 툴체인을 올린다.
# 감사 단계를 끄거나 결과를 무시하지 않는다(AGENTS.md).
#
# 구현 메모: backtest_be_go/Dockerfile의 audit 스테이지를 빌드한다. 바인드 마운트(docker run -v)를
# 쓰지 않는 이유는 Jenkins가 컨테이너 안에서 호스트 Docker 데몬에 붙어 sibling 컨테이너를 띄우기
# 때문이다. -v의 소스 경로가 호스트 기준으로 해석되어 워크스페이스 파일을 찾지 못한다(빌드 #20 실패).
# 빌드 컨텍스트는 데몬으로 스트리밍되므로 두 환경에서 모두 동작한다.
#
# 사용: scripts/audit-deps.sh [be|all]
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

audit_backend() {
  echo "== BE: govulncheck =="
  docker build --target audit --output=type=cacheonly "${REPO_ROOT}/backtest_be_go"
}

case "${1:-all}" in
  be) audit_backend ;;
  all) audit_backend ;;
  *) echo "사용법: $0 [be|all]" >&2; exit 2 ;;
esac
