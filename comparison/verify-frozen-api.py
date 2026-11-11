"""Check that every timed workload returns a populated, finite calculation."""
import json
import math
from pathlib import Path
from urllib.request import Request,urlopen

root=Path('/reports/corrected-2026-11-11')
inputs=root/'benchmark-inputs'
results=[]
for row in json.loads((inputs/'normal.json').read_text()):
    case=json.loads((inputs/'normal'/row['name']/'input.json').read_text())
    for server in ['python','rust']:
        req=Request('http://memory-'+server+'-api:8000'+case['path'],data=json.dumps(case['body']).encode(),headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=60) as response:
            assert response.status==200
            body=json.load(response)
        assert body['status']=='success'
        d=body['data'];stats=d['portfolio_statistics']
        assert math.isfinite(stats['Final_Value']) and stats['Final_Value']>=0
        assert math.isfinite(stats['Initial_Value']) and stats['Initial_Value']>0
        expected={a['symbol'] for a in case['body']['portfolio'] if a.get('asset_type')!='cash' and (a.get('amount',0)>0 or a.get('weight',0)>0)}
        present={a['symbol'] for a in d['portfolio_composition']}
        assert expected<=present,(server,case['name'],expected-present)
        results.append({'server':server,'case':case['name'],'final':stats['Final_Value'],
            'initial':stats['Initial_Value'],'equity_points':len(d['equity_curve']),
            'composition':d['portfolio_composition'],'warnings':d.get('warnings',[])})
(root/'benchmark-verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(f'{len(results)} successful finite API results; every requested nonzero stock present')
