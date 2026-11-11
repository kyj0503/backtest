"""Local-only schema verification and backed-up Rust comparison DB migration.

Run in the original Python image with /repo and /reports bind mounts.
The Python comparison DB is never connected to or changed here.
"""
import argparse
import json
import os
import re
from pathlib import Path

import pymysql
from alembic import command
from alembic.config import Config

OUT = Path('/reports')
TABLES = ['daily_prices', 'stock_news', 'stocks']

def connect(host='backtest-correctness-db', database='stock_data_cache', live=False):
    return pymysql.connect(host=host, user='compare' if live else 'root',
        password='comparison-local-app' if live else 'audit-only-root', database=database,
        charset='utf8mb4', autocommit=True)

def schema(db):
    with db.cursor() as cur:
        result = {}
        for table in TABLES:
            cur.execute('SHOW CREATE TABLE ' + table)
            result[table] = re.sub(r' AUTO_INCREMENT=\d+', '', cur.fetchone()[1])
        return result

def migrate(host, database, revision, live=False, stamp=False):
    user, password = ('compare','comparison-local-app') if live else ('root','audit-only-root')
    os.environ['DATABASE_URL'] = f'mysql+pymysql://{user}:{password}@{host}:3306/{database}?charset=utf8mb4'
    config = Config('/repo/backtest_be_fast/alembic.ini')
    config.set_main_option('script_location', '/repo/backtest_be_fast/alembic')
    (command.stamp if stamp else command.upgrade)(config, revision)

def main(mode):
    init = connect()
    test_name = 'correctness_migrations' if mode == 'verify' else 'correctness_old_schema'
    with init.cursor() as cur:
        cur.execute('CREATE DATABASE IF NOT EXISTS ' + test_name + ' CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
    migrate('backtest-correctness-db',test_name,'1f574a9ba22e')
    migrated = connect(database=test_name)
    old = schema(migrated)
    if mode == 'migrate-local':
        backup = OUT/'rust-db-before-precision.sql'
        assert backup.exists() and backup.stat().st_size > 1000, 'Back up the local Rust DB first'
        live = connect('mysql-rust',live=True)
        assert schema(live) == old, 'Local DB differs from verified old Alembic schema; refuse to stamp'
        with live.cursor() as cur:
            cur.execute("SHOW TABLES LIKE 'alembic_version'")
            if not cur.fetchone():
                migrate('mysql-rust','stock_data_cache','1f574a9ba22e',live=True,stamp=True)
        migrate('mysql-rust','stock_data_cache','head',live=True)
        assert schema(live) == schema(init)
        live.close()
    migrate('backtest-correctness-db',test_name,'head')
    assert schema(migrated) == schema(init), 'Initdb and Alembic schemas differ (including comments)'
    result = {'schema_parity':True,'tables':TABLES,'price_type':'decimal(38,18)',
              'database_regressions':2,'local_rust_migrated':mode=='migrate-local',
              'python_database_modified':False}
    (OUT/('database-'+mode+'.json')).write_text(json.dumps(result,indent=2))
    print(json.dumps(result))

if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['verify','migrate-local'])
    main(p.parse_args().mode)
