"""Read public quote caches into benchmark evidence; never modifies either DB."""
import argparse
import json
from pathlib import Path
import pymysql

parser = argparse.ArgumentParser()
parser.add_argument('--output', default='/reports/scenarios')
out = Path(parser.parse_args().output)
out.mkdir(parents=True, exist_ok=True)
for server in ['python', 'rust']:
    db = pymysql.connect(host='mysql-'+server, user='compare', password='comparison-local-app', database='stock_data_cache', cursorclass=pymysql.cursors.DictCursor)
    histories = {}
    with db.cursor() as cursor:
        cursor.execute('SELECT id,ticker,name,exchange,info_json FROM stocks')
        for stock in cursor.fetchall():
            info = json.loads(stock['info_json'] or '{}')
            cursor.execute('SELECT date,open,high,low,close,volume FROM daily_prices WHERE stock_id=%s ORDER BY date', (stock['id'],))
            bars = [{k: str(v) if k == 'date' else float(v) for k, v in b.items()} for b in cursor.fetchall()]
            if bars:
                histories[stock['ticker']] = dict(symbol=stock['ticker'],currency=info.get('currency',''),company_name=stock['name'] or stock['ticker'],exchange=stock['exchange'] or '',first_trade_date=None,bars=bars)
    (out/('prices-'+server+'.json')).write_text(json.dumps(histories))
    print(server, {s:len(h['bars']) for s,h in histories.items()})
    db.close()
