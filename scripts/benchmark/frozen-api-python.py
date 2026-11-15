"""Benchmark-only quote adapter. Runs the unchanged Python HTTP/calculation path.

Shared frozen OHLC/FX replace external data access in both implementations.
This file is mounted into an isolated benchmark container, never installed in
the four user-facing services. Supplemental endpoints are outside this test.
"""
import json
import os
from pathlib import Path
import pandas as pd
import uvicorn
from app.services.portfolio_manager_service import portfolio_manager_service
from app.services.backtest_engine import backtest_engine
from app.repositories.stock_repository import get_stock_repository

histories=json.loads(Path(os.environ['BACKTEST_FIXTURE_FILE']).read_text())
fx={'KRW':'KRW=X','JPY':'JPY=X','EUR':'EURUSD=X'}

def frame(symbol,start=None,end=None):
    if symbol not in histories: return pd.DataFrame()
    df=pd.DataFrame(histories[symbol]['bars']).rename(columns={'date':'Date','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
    df['Date']=pd.to_datetime(df['Date']);df=df.set_index('Date')
    if start is not None: df=df[df.index>=pd.Timestamp(start)]
    if end is not None: df=df[df.index<=pd.Timestamp(end)]
    return df

class Repository:
    def load_stock_data(self,symbol,start_date=None,end_date=None,**kw): return frame(symbol,start_date,end_date)
    def get_tickers_info_batch(self,symbols): return {s:{'symbol':s,'currency':histories[s]['currency']} for s in symbols if s in histories}

class Currency:
    async def load_multiple_exchange_rates(self,currencies,**kw):
        return {c:{pd.Timestamp(b['date']).date():b['close'] for b in histories[fx[c]]['bars']} for c in currencies if c!='USD'}

async def prices(ticker,start_date,end_date): return frame(ticker,start_date,end_date)

async def convert(ticker,data,start_date,end_date):
    currency=histories[ticker]['currency']
    if currency=='USD':return data
    data=data.copy();rates=frame(fx[currency])['Close'].reindex(data.index,method='ffill')
    for col in ['Open','High','Low','Close']:
        data[col]=data[col]*rates if currency=='EUR' else data[col]/rates
    return data

portfolio_manager_service.data_loader.stock_repository=Repository()
get_stock_repository().get_tickers_info_batch=Repository().get_tickers_info_batch
portfolio_manager_service.data_loader.currency_converter=Currency()
backtest_engine._get_price_data=prices
backtest_engine._convert_to_usd=convert
uvicorn.run('app.main:app',host='0.0.0.0',port=8000,workers=1,log_level='warning')
