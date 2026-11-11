"""Run original engine with frozen Python-cache quotes, bypassing network/DB.

The repository and currency adapters supply common daily observations; this is
an engine isolation experiment, not another live API or performance benchmark.
"""
import asyncio
import json
import logging
import warnings
from pathlib import Path
from unittest.mock import patch
import pandas as pd
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.services.backtest_engine import backtest_engine
from app.utils.serializers import recursive_serialize

logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore')
root=Path('/reports/scenarios')
histories=json.loads((root/'prices-python.json').read_text())
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

async def main():
    manager=PortfolioManagerService();manager.data_loader.stock_repository=Repository();manager.data_loader.currency_converter=Currency()
    cases=[]
    with patch.object(backtest_engine,'_get_price_data',side_effect=prices),patch.object(backtest_engine,'_convert_to_usd',side_effect=convert),patch('backtesting.backtesting._tqdm',side_effect=lambda iterable,**kw:iterable):
        for folder in sorted((root/'normal').iterdir()):
            case=json.loads((folder/'input.json').read_text())
            if case['method']!='POST' or case['name']=='post_all_supplemental':continue
            request=case['body'];result=await manager.run_portfolio_backtest(PortfolioBacktestRequest(**request))
            cases.append(dict(name=case['name'],request=request,python=recursive_serialize(result)))
    (root/'replay-python.json').write_text(json.dumps(cases,allow_nan=False))
    print('Same-input Python engine cases:',len(cases))
asyncio.run(main())
