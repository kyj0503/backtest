"""Exercise the unchanged final image against an isolated disposable database."""
import json
from pathlib import Path
import urllib.error
import urllib.request

OUT=Path(__file__).resolve().parents[2]/'.comparison/reports/fourth-audit-2026-11-11'
cases=json.loads((OUT/'http-cases.json').read_text())
engine={c['name']:c['output'] for c in json.loads((OUT/'engine-results.json').read_text())}
results=[]
for c in cases:
    for attempt in range(2 if c['name']=='late_listing_cash' else 1):
        req=urllib.request.Request('http://127.0.0.1:8002/api/v1/backtest',json.dumps(c['request']).encode(),{'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=90) as r: status=r.status; body=json.load(r)
        except urllib.error.HTTPError as r:
            status=r.code;body=json.load(r)
        actual=body.get('data',{}).get('portfolio_statistics',{}).get('Final_Value')
        expected=engine[c['name']]['data']['portfolio_statistics']['Final_Value']
        results.append(dict(name=c['name'],attempt=attempt+1,status=status,engine_final=expected,http_final=actual,output=body))
        print(c['name'],attempt+1,status,actual,flush=True)
(OUT/'http-results.json').write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf8')
assert all(r['status']==200 and abs(r['http_final']-r['engine_final'])<1e-7 for r in results if r['attempt']==1)
