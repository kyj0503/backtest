"""Copy public quotes from the local Python comparison DB to Rust for fair inputs.

The Python DB is read only. This deliberately has no configurable host or DB:
it cannot target production. Back up Rust rows before a transactional update.
Run only with the comparison APIs idle, then restart them to clear RAM caches.
"""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import pymysql

parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--apply', action='store_true', required=True)
args = parser.parse_args()
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)

def connect(server):
    return pymysql.connect(host='mysql-'+server, user='compare',
        password='comparison-local-app', database='stock_data_cache',
        cursorclass=pymysql.cursors.DictCursor)

def read(db):
    result = []
    with db.cursor() as cursor:
        cursor.execute('SELECT id,ticker,name,exchange,info_json FROM stocks ORDER BY ticker')
        for stock in cursor.fetchall():
            cursor.execute('SELECT date,open,high,low,close,adj_close,volume FROM daily_prices WHERE stock_id=%s ORDER BY date', (stock['id'],))
            result.append(dict(stock=stock, bars=cursor.fetchall()))
    return result

python = connect('python')
rust = connect('rust')
try:
    reference, backup = read(python), read(rust)
    for name, data in [('python-source', reference), ('rust-before-alignment', backup)]:
        # Fail rather than overwrite previous evidence.
        with (out/(name+'.json')).open('x') as file:
            json.dump(data, file, default=str, ensure_ascii=False)
    rust.rollback()
    counts = {}
    with rust.cursor() as cursor:
        for item in reference:
            s = item['stock']
            info = json.loads(s['info_json'] or '{}')
            info['rust_chart_date_version'] = 2  # source uses yfinance historical IANA dates
            cursor.execute('INSERT INTO stocks(ticker,name,exchange,info_json,last_info_update,data_last_update) VALUES(%s,%s,%s,%s,UTC_TIMESTAMP(),UTC_TIMESTAMP()) ON DUPLICATE KEY UPDATE name=VALUES(name),exchange=VALUES(exchange),info_json=VALUES(info_json)',
                           (s['ticker'], s['name'], s['exchange'], json.dumps(info)))
            cursor.execute('SELECT id FROM stocks WHERE ticker=%s', (s['ticker'],))
            stock_id = cursor.fetchone()['id']
            # Replace only this known public quote series; preserve other tables/tickers.
            cursor.execute('DELETE FROM daily_prices WHERE stock_id=%s', (stock_id,))
            cursor.executemany('INSERT INTO daily_prices(stock_id,date,open,high,low,close,adj_close,volume) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)',
                [(stock_id, *(bar[k] for k in ['date','open','high','low','close','adj_close','volume'])) for bar in item['bars']])
            counts[s['ticker']] = len(item['bars'])
    rust.commit()
    manifest = dict(created=datetime.now(timezone.utc).isoformat(),
        source='mysql-python/stock_data_cache', target='mysql-rust/stock_data_cache',
        python_source_sha256=hashlib.sha256((out/'python-source.json').read_bytes()).hexdigest(),
        rows=counts, note='Public quotes aligned once; subsequent Yahoo fetching remains enabled.')
    (out/'alignment.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest))
finally:
    python.close()
    rust.close()
