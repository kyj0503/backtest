// k6 부하 시나리오. 환경변수: BASE(대상 URL), MODE(post|get), VUS, DURATION, OUT(요약 JSON 경로).
//   post: 32개 백테스트 요청을 가상 사용자마다 다른 순서로 돌린다(POST /api/v1/backtest).
//   get : 종목 2개 5년 시세 조회(GET /api/v1/prices).
// 가상 사용자마다 X-Forwarded-For를 달리해 서로 다른 클라이언트로 센다(클라이언트당 상한 2를 피한다).
import http from 'k6/http';
import { Counter } from 'k6/metrics';
import { SharedArray } from 'k6/data';

const MODE = __ENV.MODE || 'post';
const BASE = __ENV.BASE;
const CODES = ['200', '422', '429', '499', '500', '503', '504'];
const counters = Object.fromEntries(CODES.concat(['other']).map((c) => [c, new Counter(`status_${c}`)]));

const bodies = new SharedArray('bodies', () =>
  JSON.parse(open('/inputs/normal.json')).map((c) => JSON.stringify(JSON.parse(open(`/inputs/normal/${c.name}/input.json`)).body)),
);

export const options = {
  scenarios: { load: { executor: 'constant-vus', vus: Number(__ENV.VUS || 1), duration: __ENV.DURATION || '30s' } },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
  // 성공 응답만의 지연 시간을 요약에 싣기 위한 하위 지표(임계값은 판정에 쓰지 않는다).
  thresholds: { 'http_req_duration{expected_response:true}': ['max>=0'] },
  discardResponseBodies: true,
};

export default function () {
  const vu = __VU;
  const headers = { 'Content-Type': 'application/json', 'X-Forwarded-For': `198.18.${Math.floor(vu / 250)}.${(vu % 250) + 1}` };
  let res;
  if (MODE === 'get') {
    res = http.get(`${BASE}/api/v1/prices?symbols=AAPL&symbols=MSFT&start_date=2020-01-02&end_date=2024-12-31`, { headers, timeout: '120s' });
  } else {
    const body = bodies[(__ITER * 7 + vu * 13) % bodies.length];
    res = http.post(`${BASE}/api/v1/backtest`, body, { headers, timeout: '120s' });
  }
  const code = String(res.status);
  (counters[code] || counters.other).add(1);
}

export function handleSummary(data) {
  return { [__ENV.OUT]: JSON.stringify(data) };
}
