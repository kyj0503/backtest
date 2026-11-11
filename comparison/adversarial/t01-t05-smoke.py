"""Smoke the deployed local app and production proxy using actual HTTP."""
import json
import math
from pathlib import Path
import urllib.request

OUT=Path(__file__).resolve().parents[2]/'.comparison/reports/t01-t05-2026-11-11'
rows=[]
for port,path in [(8000,'/health'),(8001,'/health/ready'),(5173,'/backtest'),(5174,'/backtest'),(5176,'/health')]:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=30) as r:assert r.status==200
    rows.append(dict(port=port,path=path,status=200))
body=dict(portfolio=[dict(symbol='AAPL',amount=10000),dict(symbol='005930.KS',amount=10000)],start_date='2023-01-02',end_date='2023-02-10',commission=.01,rebalance_frequency='none')
body.update({'include_'+k:False for k in ['stock_data','volatility_events','exchange_rates','benchmarks','news']})
requests=[('live_usd_krw',5174,body),('production_proxy',5176,json.loads((OUT/'http-cases.json').read_text())[-1]['request'])]
for name,port,body in requests:
    req=urllib.request.Request(f'http://127.0.0.1:{port}/api/v1/backtest',json.dumps(body).encode(),{'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=100) as r:status=r.status;value=json.load(r)
    d=value['data'];s=d['portfolio_statistics']
    assert abs((math.prod(1+x/100 for x in d['daily_returns'].values())-1)*100-s['Time_Weighted_Return'])<1e-7
    assert abs(sum(v['final_value'] for v in d['individual_returns'].values())-s['Final_Value'])<1e-7
    assert not d.get('warnings'),d.get('warnings')
    rows.append(dict(name=name,port=port,status=status,output=value))
(OUT/'local-smoke.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps([{'name':r.get('name',r.get('path')),'port':r['port'],'status':r['status']} for r in rows]))
