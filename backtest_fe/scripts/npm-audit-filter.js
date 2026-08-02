#!/usr/bin/env node
/**
 * `npm audit --json` 결과에서 예외 목록에 없는 high 이상 취약점만 걸러 실패시킨다.
 *
 * npm audit는 어드바이저리 단위 allowlist를 지원하지 않는다. 또 취약 패키지가
 * 전이 의존성이면 항목의 `via`에 어드바이저리 객체가 아니라 상위 패키지 "이름"이
 * 문자열로 들어오므로, 그 이름을 따라가며 실제 어드바이저리 ID를 모아야 한다.
 *
 * 사용: node npm-audit-filter.js <audit.json> [allowlist를 공백으로 구분]
 * 종료 코드: 0 = 통과(또는 전부 예외), 1 = 차단할 취약점 있음
 */
const fs = require('fs');

const [, , auditPath, allowlistRaw = ''] = process.argv;
const allow = new Set(allowlistRaw.split(/\s+/).filter(Boolean));

const report = JSON.parse(fs.readFileSync(auditPath, 'utf8'));
const vulns = report.vulnerabilities || {};
const BLOCKING_SEVERITIES = new Set(['high', 'critical']);

/** 한 항목의 어드바이저리 ID를 전이 참조까지 따라가며 수집한다. */
function advisoryIds(name, seen = new Set()) {
  if (seen.has(name)) return [];
  seen.add(name);

  const entry = vulns[name];
  if (!entry) return [];

  const ids = [];
  for (const via of entry.via || []) {
    if (typeof via === 'object' && via.url) {
      ids.push(via.url.split('/').pop());
    } else if (typeof via === 'string') {
      ids.push(...advisoryIds(via, seen));
    }
  }
  return ids;
}

const blocking = [];
let exempted = 0;

for (const [name, entry] of Object.entries(vulns)) {
  if (!BLOCKING_SEVERITIES.has(entry.severity)) continue;

  const ids = advisoryIds(name);
  // ID를 하나도 확인할 수 없으면 안전한 쪽으로 차단한다.
  if (ids.length > 0 && ids.every((id) => allow.has(id))) {
    exempted += 1;
    continue;
  }
  blocking.push({ name, severity: entry.severity, ids });
}

if (blocking.length > 0) {
  console.error('차단되는 취약점:');
  for (const v of blocking) {
    console.error(`  - ${v.name} (${v.severity}): ${v.ids.join(', ') || '어드바이저리 ID 확인 불가'}`);
  }
  console.error('\n업그레이드하거나, 도달 불가능함을 확인했다면 scripts/audit-deps.sh의 예외 목록에 근거와 함께 추가할 것.');
  process.exit(1);
}

console.log(`통과 (예외 처리된 high 이상: ${exempted}건)`);
