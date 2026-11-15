"""k6 요약 JSON과 docker stats 표본을 구현·모드·동시 사용자별 표(Markdown)로 만든다."""
import json, os, re, sys

root = sys.argv[1] if len(sys.argv) > 1 else '/reports'
IMPLS = ['python', 'rust', 'go']
CODES = ['200', '422', '429', '499', '500', '503', '504', 'other']


def mem_mib(s):
    m = re.match(r'([\d.]+)\s*([KMG]i?B)', s.strip())
    if not m:
        return None
    v, u = float(m.group(1)), m.group(2)
    return v * {'KiB': 1 / 1024, 'MiB': 1, 'GiB': 1024, 'kB': 1 / 1024, 'MB': 1, 'GB': 1024}.get(u, 1)


def stats(path):
    cpu, mem = [], []
    if os.path.exists(path):
        for line in open(path):
            if ';' not in line:
                continue
            c, m = line.split(';', 1)
            try:
                cpu.append(float(c.strip().rstrip('%')))
            except ValueError:
                pass
            v = mem_mib(m.split('/')[0])
            if v is not None:
                mem.append(v)
    avg = sum(cpu) / len(cpu) if cpu else float('nan')
    return avg, max(cpu, default=float('nan')), max(mem, default=float('nan'))


def row(impl, mode, vus):
    p = f'{root}/{impl}-{mode}-{vus}.json'
    if not os.path.exists(p):
        return None
    m = json.load(open(p))['metrics']
    total = m['http_reqs']['values']['count']
    ok = m.get('status_200', {}).get('values', {}).get('count', 0)
    dur = m['http_req_duration']['values']
    okd = m.get('http_req_duration{expected_response:true}', {}).get('values', {})
    rate = m['http_reqs']['values']['rate']
    fails = {c: int(m[f'status_{c}']['values']['count']) for c in CODES if c != '200' and f'status_{c}' in m}
    cpu_avg, cpu_max, mem_max = stats(f'{root}/{impl}-{mode}-{vus}.stats')
    return {
        'impl': impl, 'vus': vus, 'reqs': int(total), 'ok': int(ok), 'rps_ok': rate * (ok / total if total else 0),
        'p50': okd.get('med', float('nan')), 'p95': okd.get('p(95)', float('nan')), 'p99': okd.get('p(99)', float('nan')),
        'max': dur.get('max'), 'err': (total - ok) / total * 100 if total else 0,
        'fails': ', '.join(f'{c}×{n}' for c, n in fails.items() if n) or '-', 'cpu_avg': cpu_avg, 'cpu_max': cpu_max, 'mem_max': mem_max,
    }


def levels(mode):
    out = set()
    for f in os.listdir(root):
        m = re.match(rf'(\w+)-{mode}-(\d+)\.json$', f)
        if m:
            out.add(int(m.group(2)))
    return sorted(out)


for mode, title in [('post', 'POST /api/v1/backtest (32개 시나리오 혼합)'), ('get', 'GET /api/v1/prices (2종목·5년)')]:
    print(f'\n### {title}\n')
    print('| 구현 | 동시 사용자 | 요청 | 성공 RPS | p50 ms | p95 ms | p99 ms | 최대 ms | 실패 % | 실패 내역 | CPU 평균 % | CPU 최대 % | 메모리 최대 MiB |')
    print('|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|')
    for vus in levels(mode):
        for impl in IMPLS:
            r = row(impl, mode, vus)
            if r:
                print(f"| {impl} | {vus} | {r['reqs']} | {r['rps_ok']:.1f} | {r['p50']:.0f} | {r['p95']:.0f} | {r['p99']:.0f} | {r['max']:.0f} | "
                      f"{r['err']:.1f} | {r['fails']} | {r['cpu_avg']:.0f} | {r['cpu_max']:.0f} | {r['mem_max']:.0f} |")

print('\n### 메모리(MiB): 기동 직후 / 예열 후\n')
print('| 구현 | 기동 직후 | 예열 후 |')
print('|---|---:|---:|')
for impl in IMPLS:
    vals = []
    for k in ('idle', 'warm'):
        p = f'{root}/{impl}-{k}.mem'
        vals.append(f'{mem_mib(open(p).read().split("/")[0]):.0f}' if os.path.exists(p) else '-')
    print(f'| {impl} | {vals[0]} | {vals[1]} |')
