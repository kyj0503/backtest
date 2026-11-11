"""Explicitly export immutable comparison fixtures using the retained Python backend.

Run inside the Python test image with /reference (old app) and /rust (this crate).
Never run this as part of the Rust test target: expected values must not self-update.
"""
import asyncio
import json
import logging
import math
import warnings
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from backtesting import Backtest
from app.services.strategy_service import STRATEGIES

from app.main import app
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService
from app.services.backtest_engine import backtest_engine
from app.utils.serializers import recursive_serialize

logging.disable(logging.CRITICAL)
warnings.filterwarnings('ignore', category=Warning)
OUT = Path('/rust/tests/fixtures')
OUT.mkdir(parents=True, exist_ok=True)
dates = pd.bdate_range('2023-01-02', '2023-10-31')
histories = {}
for symbol, currency, base, phase in [('AAPL','USD',100,0),('MSFT','USD',70,2),('005930.KS','KRW',60000,4),('KRW=X','KRW',1300,1),('^GSPC','USD',4000,0),('^IXIC','USD',12000,2)]:
    bars = []
    for i, day in enumerate(dates):
        if symbol == 'MSFT' and i % 19 == 0:
            continue
        close = base * (1 + 0.001*i + 0.18*math.sin(i/7+phase) + 0.02*math.cos(i/2))
        open_ = close * (1 + 0.012*math.sin(i+phase))
        bars.append(dict(date=day.strftime('%Y-%m-%d'),open=open_,high=max(open_,close)*1.01,low=min(open_,close)*0.99,close=close,volume=100000+i))
    histories[symbol] = dict(symbol=symbol,currency=currency,company_name=symbol,exchange='TEST',first_trade_date=None,bars=bars)

def frame(symbol, start=None, end=None):
    records=histories[symbol]['bars']
    df=pd.DataFrame(records).rename(columns={'date':'Date','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
    df['Date']=pd.to_datetime(df['Date']);df=df.set_index('Date')
    if start is not None: df=df[df.index>=pd.Timestamp(start)]
    if end is not None: df=df[df.index<=pd.Timestamp(end)]
    return df

class Repository:
    def load_stock_data(self,symbol,start_date=None,end_date=None,**kw):
        return frame(symbol,start_date,end_date) if symbol in histories else pd.DataFrame()
    def get_tickers_info_batch(self,symbols):
        return {s:{'symbol':s,'currency':histories[s]['currency']} for s in symbols if s in histories}

class Currency:
    async def load_multiple_exchange_rates(self,currencies,**kw):
        return {c:{pd.Timestamp(b['date']).date():b['close'] for b in histories['KRW=X']['bars']} for c in currencies}

async def prices(ticker,start_date,end_date):
    return frame(ticker,start_date,end_date)

async def convert(ticker,data,start_date,end_date):
    if histories[ticker]['currency']=='USD':return data
    data=data.copy();rates=frame('KRW=X')['Close'].reindex(data.index,method='ffill')
    for col in ['Open','High','Low','Close']:data[col]=data[col]/rates
    return data

async def main():
    manager=PortfolioManagerService();manager.data_loader.stock_repository=Repository();manager.data_loader.currency_converter=Currency()
    cases=[]
    def add(name,portfolio,**kw):
        request=dict(portfolio=portfolio,start_date='2023-01-02',end_date='2023-10-31',strategy='buy_hold_strategy',rebalance_frequency='none',commission=0.002,include_stock_data=False,include_volatility_events=False,include_exchange_rates=False,include_benchmarks=False,include_news=False)
        request.update(kw);cases.append(dict(name=name,request=request))
    add('lump-sum',[dict(symbol='AAPL',amount=10000)])
    add('mixed-currency',[dict(symbol='AAPL',amount=10000),dict(symbol='005930.KS',amount=10000),dict(symbol='현금',amount=4000,asset_type='cash')])
    add('cash-only',[dict(symbol='현금',amount=1000,asset_type='cash'),dict(symbol='현금',amount=500,asset_type='cash')])
    add('zero-weight',[dict(symbol='AAPL',weight=100),dict(symbol='MSFT',weight=0)])
    for frequency in ['weekly_1','weekly_2','monthly_1','monthly_2','monthly_3','monthly_6']:
        add('dca-'+frequency,[dict(symbol='AAPL',amount=1000,investment_type='dca',dca_frequency=frequency)])
        add('rebalance-'+frequency,[dict(symbol='AAPL',amount=10000),dict(symbol='MSFT',amount=8000),dict(symbol='현금',amount=2000,asset_type='cash')],rebalance_frequency=frequency)
    add('dca-weight-rebalance',[dict(symbol='AAPL',weight=60,investment_type='dca',dca_frequency='weekly_2'),dict(symbol='MSFT',weight=30),dict(symbol='현금',weight=10,asset_type='cash')],rebalance_frequency='monthly_1')
    add('holiday-catchup',[dict(symbol='MSFT',amount=1000,investment_type='dca',dca_frequency='weekly_1'),dict(symbol='AAPL',amount=1000)],start_date='2023-01-01',end_date='2023-03-31',rebalance_frequency='monthly_1')
    add('duplicate-cash',[dict(symbol='AAPL',amount=1000),dict(symbol='예금',amount=500,asset_type='cash'),dict(symbol='예금',amount=700,asset_type='cash')],rebalance_frequency='monthly_1')
    for strategy,params in [('sma_strategy',{'short_window':5,'long_window':15}),('ema_strategy',{'fast_window':5,'slow_window':12}),('rsi_strategy',{'rsi_period':7}),('bollinger_strategy',{'period':10,'std_dev':1.5}),('macd_strategy',{'fast_period':5,'slow_period':12,'signal_period':4})]:
        for suffix,params_ in [('default',{}),('custom',params)]:
            add(strategy+'-'+suffix,[dict(symbol='AAPL',amount=10000),dict(symbol='MSFT',amount=7000),dict(symbol='현금',amount=3000,asset_type='cash')],strategy=strategy,strategy_params=params_)
        add(strategy+'-krw',[dict(symbol='005930.KS',amount=10000)],strategy=strategy,strategy_params=params)
        for day in ['2023-03-09','2023-03-22','2023-04-06','2023-04-20','2023-05-03']:
            add(strategy+'-last-bar-'+day,[dict(symbol='AAPL',amount=10000)],strategy=strategy,strategy_params=params,end_date=day)
        # Locate a real last-bar buy: finalize_trades processes it after creating
        # closing orders, so it affects equity without a completed trade record.
        for count in range(24, len(dates)):
            df=frame('AAPL').iloc[:count]
            if (df.index[-1]-df.index[0]).days < 30: continue
            with patch('backtesting.backtesting._tqdm',side_effect=lambda iterable,**kw: iterable):
                stats=Backtest(df,STRATEGIES[strategy]['class'],cash=10000,spread=.002,commission=0,finalize_trades=True).run(**params)
            if stats['_strategy']._broker.trades:
                day=df.index[-1].strftime('%Y-%m-%d')
                add(strategy+'-pending-final-buy',[dict(symbol='AAPL',amount=10000)],strategy=strategy,strategy_params=params,end_date=day)
                break
        else: raise AssertionError('No final buy reference for '+strategy)
    with patch.object(backtest_engine,'_get_price_data',side_effect=prices),patch.object(backtest_engine,'_convert_to_usd',side_effect=convert):
        for case in cases:
            result=await manager.run_portfolio_backtest(PortfolioBacktestRequest(**case['request']))
            case['expected']=recursive_serialize(result)
            print(case['name'],flush=True)
    (OUT/'histories.json').write_text(json.dumps(histories,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    (OUT/'parity.json').write_text(json.dumps(cases,ensure_ascii=False,allow_nan=False),encoding='utf-8')
    Path('/rust/openapi.json').write_text(json.dumps(app.openapi(),ensure_ascii=False),encoding='utf-8')

asyncio.run(main())
