"""HTTP smoke for a running Rust fixture or live-data server (stdlib only)."""
import argparse
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument('base_url')
parser.add_argument('--live', action='store_true')
args = parser.parse_args()

def request(path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = Request(args.base_url.rstrip('/')+path, data=data, headers={'Content-Type':'application/json'})
    with urlopen(req, timeout=90) as response:
        assert response.status == 200
        return json.load(response)

case = json.loads((Path(__file__).parent/'fixtures/parity.json').read_text())[0]
body = case['request']
if args.live:
    body['portfolio'] = [{'symbol':'AAPL','amount':10000},{'symbol':'005930.KS','amount':10000}]
result = request('/api/v1/backtest',body)
assert result['status'] == 'success', result
value = result['data']['portfolio_statistics']['Final_Value']
assert math.isfinite(value) and value > 0
if not args.live:
    expected = case['expected']['data']['portfolio_statistics']['Final_Value']
    assert math.isclose(value,expected,rel_tol=1e-6)
print('POST calculation:',result['status'], 'final value:',round(value,4))
for path, field in [
    ('prices?symbols=AAPL&start_date=2023-01-02&end_date=2023-10-31','stock_data'),
    ('exchange-rates?start_date=2023-01-02&end_date=2023-10-31','exchange_rates'),
    ('benchmarks?start_date=2023-01-02&end_date=2023-10-31','benchmarks'),
    ('news?symbols=AAPL&limit=15','news'),
]:
    result = request('/api/v1/'+path)
    assert result['status'] == 'success',result
    status = result['data']['supplemental_status'][field]
    assert status in ('ok','empty'),result
    if field != 'news': assert status == 'ok',result
    print('GET',path.split('?')[0]+':',status)
