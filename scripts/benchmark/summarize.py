import json, statistics
r = {k: json.load(open('/reports/%s.json' % k)) for k in ['python', 'rust', 'go']}
def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = int(k)
    return v[f] + (v[min(f + 1, len(v) - 1)] - v[f]) * (k - f)
def med(rep, n):
    c = [c for c in rep['cases'] if c['name'] == n][0]
    return statistics.median(x['ms'] for x in c['responses'])
total = ok = 0
for rep in r.values():
    for c in rep['cases']:
        for x in c['responses']:
            total += 1; ok += x['status'] == 200
print('requests', total, 'ok', ok)
for k, rep in r.items():
    s = [x['ms'] for c in rep['cases'] if c['concurrency'] == 1 for x in c['responses']]
    print(f"{k:6s} median={statistics.median(s):.2f} p95={pct(s,.95):.2f} peak={rep['end']['kernel_peak']/2**20:.2f}MiB idle={rep['idle']['current']/2**20:.2f}MiB events={rep['memory_events'].split()}")
labels = {'usd_single': 'AAPL 단일 종목', 'usd_five_8years': '미국 5종목·8년', 'dca_monthly_1': '매월 적립·5년',
          'rebalance_monthly_1': '매월 리밸런싱·5년', 'sma_default': 'SMA 전략·5년', 'concurrent_16': '동시 16건'}
for n, l in labels.items():
    p, ru, g = med(r['python'], n), med(r['rust'], n), med(r['go'], n)
    print(f"{l}\t{p:.2f}\t{ru:.2f}\t{g:.2f}\tpy/go {p/g:.1f}\tgo/rust {g/ru:.2f}")
