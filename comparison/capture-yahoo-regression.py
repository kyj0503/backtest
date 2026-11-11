"""Freeze public Yahoo responses with independent stdlib OHLC/date expectations.

Run in the Python Docker image (its OS includes the IANA timezone database).
No original Python backtest code or outputs are used.
"""
import datetime as dt
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

base = Path('/repo')
reports = base/'.comparison/reports/yahoo-client-2026-11-11'
cases = []
for symbol in ['AAPL','005930.KS','7203.T','KRW=X','EURUSD=X','SAP.DE','BTC-USD']:
    directory = 'live' if symbol == 'EURUSD=X' else 'live-confirmed'
    raw = json.loads((reports/directory/(symbol.replace('=','_')+'-raw.json')).read_text())
    r = raw['chart']['result'][0]
    quotes = r['indicators']['quote'][0]
    adjusted = r['indicators'].get('adjclose',[{}])[0].get('adjclose',[None]*len(r['timestamp']))
    expected = {}
    for i, timestamp in enumerate(r['timestamp']):
        day = dt.datetime.fromtimestamp(timestamp, ZoneInfo(r['meta']['exchangeTimezoneName'])).date().isoformat()
        o,h,l,c = [quotes[key][i] for key in ['open','high','low','close']]
        if not all(v is not None and math.isfinite(v) and v>0 for v in [o,h,l,c]) or h<l:
            continue
        close = adjusted[i] if adjusted[i] is not None else c
        ratio = close/c
        expected.setdefault(day,dict(date=day,open=o*ratio,high=h*ratio,low=l*ratio,close=close,volume=quotes['volume'][i] or 0))
    cases.append(dict(symbol=symbol,raw=raw,currency=r['meta']['currency'],expected=[expected[k] for k in sorted(expected)]))
output = base/'backtest_be_rust/tests/fixtures/yahoo-chart-regression.json'
assert not output.exists(), 'Do not silently replace the captured regression oracle'
output.write_text(json.dumps({'captured_on':'2026-11-11','basis':'Independent datetime.zoneinfo and arithmetic over frozen provider payloads','cases':cases},indent=2)+'\n')
print(json.dumps({'cases':len(cases),'bars':sum(len(c['expected']) for c in cases),'bytes':output.stat().st_size}))
