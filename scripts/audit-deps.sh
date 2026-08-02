#!/usr/bin/env sh
# 의존성 취약점 감사 (CI 게이트)
#
# high 이상 취약점이 있으면 종료 코드 1로 배포를 막는다. 단, 아래
# ALLOWLIST에 명시된 건은 통과시킨다 — 업그레이드로 해결할 수 없고 이 앱의
# 실제 사용 경로에서 도달 불가능한 것들이다.
#
# 예외를 두는 이유: 고칠 수 없는 취약점 때문에 게이트가 영구히 빨간불이면
# 사람이 게이트 자체를 꺼버린다. 그러면 "고칠 수 있는" 새 취약점도 함께
# 놓친다. 예외는 반드시 근거와 재검토 조건을 함께 적을 것.
#
# 사용: scripts/audit-deps.sh [fe|be]
set -eu

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# --- 예외 목록 ---------------------------------------------------------------
# GHSA-qwww-vcr4-c8h2 (react-router 7.12.0-8.2.0, high)
#   RSC(React Server Components) 모드 전용 CSRF 우회. 이 앱은 BrowserRouter만
#   쓰고 RSC를 쓰지 않는다. 7.x 라인에 수정 버전이 없어(현재 최신 7.18.2도
#   범위 내) 업그레이드로 해결 불가.
#   재검토: 8.x로 올리거나 7.x 패치가 나오면 제거할 것.
NPM_ALLOWLIST="GHSA-qwww-vcr4-c8h2"

# PYSEC-2026-1223 / CVE-2026-21883 (bokeh 2.4.3)
#   bokeh 서버의 Origin 검증 우회. bokeh는 backtesting==0.3.3이 끌어오는 전이
#   의존성이고(CLAUDE.md 제약 2에 따라 의도적으로 고정), 이 앱은 .plot()을
#   호출하지 않아 bokeh 서버를 띄우지 않는다.
#   재검토: backtesting 핀을 풀면 함께 제거할 것.
PIP_IGNORE="PYSEC-2026-1223"
# -----------------------------------------------------------------------------

audit_frontend() {
  echo "== FE: npm audit (high 이상, 예외: ${NPM_ALLOWLIST}) =="
  docker run --rm \
    -v "${REPO_ROOT}/backtest_fe:/app:ro" \
    -v "${REPO_ROOT}/scripts/npm-audit-filter.js:/filter.js:ro" \
    -w /app node:22-alpine \
    sh -c "npm audit --audit-level=high --json > /tmp/a.json 2>/dev/null || true; \
           node /filter.js /tmp/a.json '${NPM_ALLOWLIST}'"
}

audit_backend() {
  echo "== BE: pip-audit (예외: ${PIP_IGNORE}) =="
  ignore_args=""
  for vuln in ${PIP_IGNORE}; do
    ignore_args="${ignore_args} --ignore-vuln ${vuln}"
  done
  # shellcheck disable=SC2086
  docker run --rm -v "${REPO_ROOT}/backtest_be_fast:/app:ro" -w /app python:3.11-slim \
    sh -c "pip install -q pip-audit && pip-audit -r requirements.lock.txt ${ignore_args}"
}

case "${1:-all}" in
  fe) audit_frontend ;;
  be) audit_backend ;;
  all) audit_frontend; audit_backend ;;
  *) echo "사용법: $0 [fe|be|all]" >&2; exit 2 ;;
esac
