"""Read-only probe of historical chart timestamp interpretation."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from curl_cffi import requests

response=requests.get('https://query1.finance.yahoo.com/v8/finance/chart/KRW=X', params=dict(period1=int(datetime(2023,4,10,tzinfo=timezone.utc).timestamp()),period2=int(datetime(2023,4,15,tzinfo=timezone.utc).timestamp()),interval='1d',events='div,splits'),impersonate='chrome',timeout=30)
response.raise_for_status()
chart=response.json()['chart']['result'][0]
meta=chart['meta']
records=[]
for i,timestamp in enumerate(chart['timestamp']):
    utc=datetime.fromtimestamp(timestamp,timezone.utc)
    records.append(dict(utc=utc.isoformat(),fixed_offset_date=str((utc+timedelta(seconds=meta['gmtoffset'])).date()),timezone_date=str(utc.astimezone(ZoneInfo(meta['exchangeTimezoneName'])).date()),close=chart['indicators']['quote'][0]['close'][i]))
out=dict(timezone=meta['exchangeTimezoneName'],gmtoffset=meta['gmtoffset'],records=records)
Path('/reports/scenarios/yahoo-date-probe.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out))
