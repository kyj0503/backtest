import json, sys, time, urllib.request
order = json.load(open('/inputs/normal.json'))
fails = 0
for srv in ['python', 'rust', 'go']:
    base = 'http://bench-%s-api:8000' % srv
    for _ in range(90):
        try:
            urllib.request.urlopen(base + '/health', timeout=2); break
        except Exception:
            time.sleep(1)
    bad = []
    for row in order:
        case = json.load(open('/inputs/normal/%s/input.json' % row['name']))
        req = urllib.request.Request(base + case['path'], data=json.dumps(case['body']).encode(), method=case['method'], headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                st = r.status; d = json.load(r)
        except urllib.error.HTTPError as e:
            st = e.code; d = json.load(e)
        if st != 200 or 'portfolio_statistics' not in d.get('data', {}):
            bad.append((row['name'], st))
    fails += len(bad)
    print(srv, 'scenarios', len(order), 'ok', len(order) - len(bad), 'failed', bad, flush=True)
sys.exit(1 if fails else 0)
