#!/usr/bin/env sh
# 의존성 취약점 감사 (CI 배포 전 검사)
#
#   be | go   Go 백엔드: govulncheck (코드에서 실제로 호출되는 취약 함수만 보고, 예외 목록 없음)
#   python    Python 원본: pip-audit (requirements.lock.txt)
#   rust      Rust 구현: cargo-audit (Cargo.lock)
#   all       셋 다
#
# 결과가 나오면 모듈·패키지·툴체인을 올린다. 감사 단계를 끄거나 결과를 무시하지 않는다(AGENTS.md).
#
# 구현 메모: 각 Dockerfile의 audit 스테이지를 빌드한다. 바인드 마운트(docker run -v)를 쓰지 않는 이유는
# Jenkins가 컨테이너 안에서 호스트 Docker 데몬에 붙어 sibling 컨테이너를 띄우기 때문이다. -v의 소스 경로가
# 호스트 기준으로 해석되어 워크스페이스 파일을 찾지 못한다(빌드 #20 실패). 빌드 컨텍스트는 데몬으로
# 스트리밍되므로 두 환경에서 모두 동작한다.
#
# 사용: scripts/audit-deps.sh [be|go|python|rust|all]
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Python 원본에서 업그레이드로 고칠 수 없고 도달 불가능한 취약점 ID(공백 구분). 근거와 재검토 조건을 함께 적는다.
PIP_IGNORE=""

audit_go() {
  echo "== Go: govulncheck =="
  docker build --target audit --output=type=cacheonly "${REPO_ROOT}/backtest_be_go"
}

audit_python() {
  echo "== Python: pip-audit (예외: ${PIP_IGNORE:-없음}) =="
  docker build --target audit --output=type=cacheonly \
    --build-arg "PIP_AUDIT_IGNORE=${PIP_IGNORE}" "${REPO_ROOT}/backtest_be_python"
}

audit_rust() {
  echo "== Rust: cargo-audit =="
  docker build --target audit --output=type=cacheonly "${REPO_ROOT}/backtest_be_rust"
}

case "${1:-all}" in
  be|go) audit_go ;;
  python) audit_python ;;
  rust) audit_rust ;;
  all) audit_go; audit_python; audit_rust ;;
  *) echo "사용법: $0 [be|go|python|rust|all]" >&2; exit 2 ;;
esac
