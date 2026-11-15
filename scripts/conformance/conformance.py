"""세 백엔드(Python / Rust / Go)의 API 입출력 적합성 검사.

같은 고정 시세로 띄운 세 서버에 같은 요청을 보내고, 운영 기준인 Go 응답과 비교한다.
  - 상태 코드
  - 스키마: 객체 키 집합(경로별), 값의 JSON 타입(숫자·문자열·불리언·null·배열·객체)
  - 값: 숫자는 상대 오차 1e-9, 그 밖은 완전 일치(실행 시각 같은 비결정 필드는 뺀다)
  - 객체 키 순서(참고 보고만, 실패로 치지 않는다)

사용(컨테이너 안에서): python conformance.py --out /reports [--only python,rust]
요청 목록: /cases/parity.json(64), /cases/http-boundary.json(23), 아래 EXTRA 사례.
"""
import argparse, json, math, sys, urllib.request, urllib.error, collections

ap = argparse.ArgumentParser()
ap.add_argument('--out', default='/reports')
ap.add_argument('--only', default='python,rust')
ap.add_argument('--base-go', default='http://conf-go-api:8000')
ap.add_argument('--base-python', default='http://conf-python-api:8000')
ap.add_argument('--base-rust', default='http://conf-rust-api:8000')
ap.add_argument('--tolerance', type=float, default=1e-9)
args = ap.parse_args()
bases = {'go': args.base_go, 'python': args.base_python, 'rust': args.base_rust}
targets = [t for t in args.only.split(',') if t]
IGNORE = {'execution_time_seconds', 'timestamp'}

def call(base, method, path, body=None, raw=None, headers=None):
    data = raw if raw is not None else (json.dumps(body, ensure_ascii=False).encode() if body is not None else None)
    h = {'Content-Type': 'application/json'}
    h.update(headers or {})
    req = urllib.request.Request(base + path, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            status, text = r.status, r.read()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read()
    try:
        return status, json.loads(text, object_pairs_hook=collections.OrderedDict)
    except Exception:
        return status, {'__non_json__': text[:200].decode('utf-8', 'replace')}

def jtype(v):
    if v is None: return 'null'
    if isinstance(v, bool): return 'bool'
    if isinstance(v, (int, float)): return 'number'
    if isinstance(v, str): return 'string'
    if isinstance(v, list): return 'array'
    return 'object'

def compare(path, want, got, out, dynamic=False):
    tw, tg = jtype(want), jtype(got)
    if tw != tg:
        out['type'].append(f'{path}: go={tw} other={tg}')
        return
    if tw == 'object':
        kw, kg = list(want.keys()), list(got.keys())
        for k in kw:
            if k in IGNORE: continue
            if k not in got: out['missing'].append(f'{path}.{k}')
        for k in kg:
            if k in IGNORE: continue
            if k not in want: out['extra'].append(f'{path}.{k}')
        common = [k for k in kw if k in got and k not in IGNORE]
        if [k for k in kg if k in want and k not in IGNORE] != common:
            out['order'].append(path)
        for k in common:
            compare(f'{path}.{k}', want[k], got[k], out)
    elif tw == 'array':
        if len(want) != len(got):
            out['length'].append(f'{path}: go={len(want)} other={len(got)}')
        for i, (a, b) in enumerate(zip(want, got)):
            compare(f'{path}[{i}]', a, b, out)
    elif tw == 'number':
        rel = abs(want - got) / max(1.0, abs(want))
        out['max_rel'] = max(out['max_rel'], rel)
        if rel > args.tolerance:
            out['value'].append(f'{path}: go={want!r} other={got!r}')
    elif want != got:
        out['value'].append(f'{path}: go={want!r} other={got!r}')

def calc_only(body):
    b = dict(body)
    for k in ['include_stock_data', 'include_volatility_events', 'include_exchange_rates', 'include_benchmarks', 'include_news']:
        b[k] = False
    return b

cases = []
for c in json.load(open('/cases/parity.json')):
    cases.append(('parity/' + c['name'], 'POST', '/api/v1/backtest', calc_only(c['request']), None))
for c in json.load(open('/cases/parity.json'))[:6]:
    cases.append(('parity-supplemental/' + c['name'], 'POST', '/api/v1/backtest', dict(c['request'], include_news=False), None))
for c in json.load(open('/cases/http-boundary.json')):
    r = c['request']
    raw = r['raw'].encode() if r.get('raw') is not None else None
    if r['method'] == 'GET':
        cases.append(('boundary/' + c['name'], 'GET', r['path'], None, None))
    else:
        cases.append(('boundary/' + c['name'], 'POST', r['path'], r.get('body'), raw))
P = '2023-01-03'; E = '2023-10-31'
base = {'start_date': P, 'end_date': E, 'commission': 0.002, 'rebalance_frequency': 'none'}
extra = [
    ('extra/total_amount_dca', {'portfolio': [{'symbol': 'AAPL', 'amount': 333.33, 'total_amount': 3000, 'investment_type': 'dca', 'dca_frequency': 'monthly_1'}]}),
    ('extra/weights_cash', {'portfolio': [{'symbol': 'AAPL', 'weight': 60}, {'symbol': '예금', 'weight': 40, 'asset_type': 'cash'}], 'rebalance_frequency': 'monthly_1'}),
    ('extra/krw_rebalance', {'portfolio': [{'symbol': '005930.KS', 'amount': 3000}, {'symbol': 'MSFT', 'amount': 3000}], 'rebalance_frequency': 'weekly_2'}),
    ('extra/missing_symbol', {'portfolio': [{'symbol': 'AAPL', 'amount': 1000}, {'symbol': 'ZZZZ', 'amount': 500}]}),
    ('extra/all_missing', {'portfolio': [{'symbol': 'ZZZZ', 'amount': 500}]}),
    ('extra/strategy_params_string', {'portfolio': [{'symbol': 'AAPL', 'amount': 1000}], 'strategy': 'rsi_strategy', 'strategy_params': {'rsi_period': '7'}}),
    ('extra/lowercase_symbol', {'portfolio': [{'symbol': 'aapl', 'amount': 1000}]}),
    ('extra/amount_string', {'portfolio': [{'symbol': 'AAPL', 'amount': '1000'}]}),
    ('extra/future_end', {'portfolio': [{'symbol': 'AAPL', 'amount': 1000}], 'end_date': '2099-01-01'}),
    ('extra/default_rebalance_buyhold', {'portfolio': [{'symbol': 'AAPL', 'amount': 1000}, {'symbol': 'MSFT', 'amount': 1000}], 'rebalance_frequency': None}),
]
for name, b in extra:
    body = calc_only(dict(base, **b))
    if b.get('rebalance_frequency', 0) is None:
        body.pop('rebalance_frequency')
    cases.append((name, 'POST', '/api/v1/backtest', body, None))
cases += [
    ('extra/invalid_utf8', 'POST', '/api/v1/backtest', None, b'{"portfolio":[{"symbol":"\xbf\xb9","amount":1,"asset_type":"cash"}],"start_date":"2023-01-03","end_date":"2023-10-31"}'),
    ('extra/empty_body', 'POST', '/api/v1/backtest', None, b''),
    ('extra/body_array', 'POST', '/api/v1/backtest', None, b'[1,2]'),
    ('get/prices', 'GET', f'/api/v1/prices?symbols=AAPL&symbols=msft&start_date=2023-01-02&end_date={E}', None, None),
    ('get/exchange_rates', 'GET', f'/api/v1/exchange-rates?start_date=2023-01-02&end_date={E}', None, None),
    ('get/benchmarks', 'GET', f'/api/v1/benchmarks?start_date=2023-01-02&end_date={E}', None, None),
    ('get/news', 'GET', '/api/v1/news?symbols=AAPL&limit=5', None, None),
    ('get/prices_missing_symbol', 'GET', f'/api/v1/prices?symbols=ZZZZ&start_date=2023-01-02&end_date={E}', None, None),
    ('get/bad_symbol', 'GET', f'/api/v1/prices?symbols=A%3CB&start_date=2023-01-02&end_date={E}', None, None),
    ('get/dup_lower_symbols', 'GET', f'/api/v1/prices?symbols=msft&symbols=AAPL&symbols=aapl&start_date=2023-01-02&end_date={E}', None, None),
    ('get/mixed_missing_symbol', 'GET', f'/api/v1/prices?symbols=AAPL&symbols=ZZZZ&start_date=2023-01-02&end_date={E}', None, None),
    ('get/end_before_start', 'GET', '/api/v1/prices?symbols=AAPL&start_date=2023-03-02&end_date=2023-02-01', None, None),
    ('get/future_end', 'GET', '/api/v1/exchange-rates?start_date=2023-01-02&end_date=2099-02-01', None, None),
    ('get/too_long_period', 'GET', '/api/v1/benchmarks?start_date=2003-01-02&end_date=2023-02-01', None, None),
    ('get/bad_month', 'GET', '/api/v1/prices?symbols=AAPL&start_date=2023-13-02&end_date=2023-02-01', None, None),
    ('get/short_date_and_bad_symbol', 'GET', '/api/v1/prices?symbols=A%3CB&start_date=2023-1-2&foo=1', None, None),
    ('get/bad_day_sep', 'GET', '/api/v1/benchmarks?start_date=2023/01/02&end_date=2023-02-30', None, None),
    ('get/datetime_zero', 'GET', '/api/v1/benchmarks?start_date=2023-01-02T00:00:00&end_date=2023-02-01%2010:00', None, None),
    ('get/limit_abc', 'GET', '/api/v1/news?symbols=AAPL&limit=abc', None, None),
    ('get/limit_21', 'GET', '/api/v1/news?symbols=AAPL&limit=21', None, None),
    ('get/empty_symbol', 'GET', '/api/v1/news?symbols=', None, None),
    ('get/long_symbol', 'GET', '/api/v1/news?symbols=ABCDEFGHIJK', None, None),
    ('get/korean_symbol', 'GET', '/api/v1/news?symbols=%EC%98%88%EA%B8%88', None, None),
    ('get/cash_symbol', 'GET', '/api/v1/news?symbols=cash', None, None),
    ('get/21_symbols', 'GET', '/api/v1/news?' + '&'.join('symbols=' + chr(65 + i) for i in range(21)), None, None),
    ('get/no_args', 'GET', '/api/v1/prices', None, None),
    ('misc/health', 'GET', '/health', None, None),
    ('misc/ready', 'GET', '/health/ready', None, None),
    ('misc/not_found', 'GET', '/api/v1/nope', None, None),
    ('misc/method_not_allowed', 'GET', '/api/v1/backtest', None, None),
]

report = {t: {} for t in targets}
summary = {t: collections.Counter() for t in targets}
for name, method, path, body, raw in cases:
    gs, gb = call(bases['go'], method, path, body, raw)
    for t in targets:
        s, b = call(bases[t], method, path, body, raw)
        out = {'go_status': gs, 'status': s, 'type': [], 'missing': [], 'extra': [], 'value': [], 'length': [], 'order': [], 'max_rel': 0.0}
        if name in ('misc/health', 'misc/ready'):
            # timestamp·version 형식만 본다
            gb2 = {k: v for k, v in gb.items() if k not in ('timestamp',)}
            b2 = {k: v for k, v in b.items() if k not in ('timestamp',)}
            compare('$', gb2, b2, out)
        else:
            compare('$', gb, b, out)
        ok = s == gs and not any(out[k] for k in ('type', 'missing', 'extra', 'value', 'length'))
        out['ok'] = ok
        report[t][name] = out
        summary[t]['ok' if ok else 'diff'] += 1
        if s != gs: summary[t]['status_diff'] += 1

json.dump(report, open(f'{args.out}/conformance.json', 'w'), ensure_ascii=False, indent=1)
for t in targets:
    print(f'== {t}: {dict(summary[t])} of {len(cases)} cases')
    agg = collections.Counter()
    for name, o in report[t].items():
        if o['ok']: continue
        for k in ('missing', 'extra', 'type', 'value', 'length'):
            for p in o[k]:
                key = p.split(':')[0]
                # 경로의 배열 첨자·날짜 키를 일반화해 집계한다
                import re
                key = re.sub(r'\[\d+\]', '[]', key)
                key = re.sub(r'\.\d{4}-\d{2}-\d{2}', '.<date>', key)
                agg[(k, name.split('/')[0], key)] += 1
    for (k, grp, key), n in sorted(agg.items(), key=lambda x: (-x[1], x[0]))[:120]:
        print(f'  {k:7s} {grp:20s} {n:5d}  {key}')
    st = [(n, o['go_status'], o['status']) for n, o in report[t].items() if o['status'] != o['go_status']]
    for n, a, b in st:
        print(f'  status  {n}: go={a} {t}={b}')
