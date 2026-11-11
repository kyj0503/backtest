"""Compare running Python and Rust HTTP services; never changes application code.

Run in a Python container on backtest-compare_default with /reports mounted.
Stores complete inputs/responses plus timings so differences can be reproduced.
"""
import argparse
import collections
import concurrent.futures
import copy
import hashlib
import json
import math
import statistics
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

parser = argparse.ArgumentParser()
parser.add_argument('--output', default='/reports/scenarios')
parser.add_argument('--phase', choices=['normal','boundary','concurrent','all'], default='all')
args = parser.parse_args()
OUT = Path(args.output)
OUT.mkdir(parents=True, exist_ok=True)
SERVERS = {'python':'http://python-api:8000','rust':'http://rust-api:8000'}
BASE = dict(portfolio=[dict(symbol='AAPL',amount=10000)], start_date='2023-01-03',end_date='2023-10-31',strategy='buy_hold_strategy',rebalance_frequency='none',commission=.002,
            include_stock_data=False,include_volatility_events=False,include_exchange_rates=False,include_benchmarks=False,include_news=False)

def make(name, portfolio=None, **changes):
    body = copy.deepcopy(BASE)
    if portfolio is not None: body['portfolio'] = portfolio
    body.update(changes)
    return {'name':name,'method':'POST','path':'/api/v1/backtest','body':body}

def call(server, case, headers=None):
    body = case.get('body')
    raw = case.get('raw')
    if raw is None and body is not None: raw = json.dumps(body,ensure_ascii=False).encode()
    request = Request(SERVERS[server]+case['path'], data=raw, method=case['method'],
                      headers={'Content-Type':'application/json',**(headers or {})})
    start = time.perf_counter()
    try:
        response = urlopen(request,timeout=150)
    except HTTPError as error:
        response = error
    except (URLError,TimeoutError,ConnectionError) as error:
        return dict(status=0,ms=(time.perf_counter()-start)*1000,bytes=0,body={'transport_error':str(error)})
    with response:
        content = response.read()
        elapsed = (time.perf_counter()-start)*1000
        try: data = json.loads(content)
        except (ValueError,UnicodeError): data = {'text':content.decode(errors='replace')[:2000]}
        return dict(status=response.status,ms=elapsed,bytes=len(content),body=data,retry_after=response.headers.get('Retry-After'))

def compare(python, rust):
    a = python.get('body',{}).get('data',{})
    b = rust.get('body',{}).get('data',{})
    stats_a = a.get('portfolio_statistics',{})
    stats_b = b.get('portfolio_statistics',{})
    statistics_diff = {}
    for key in sorted(stats_a.keys() | stats_b.keys()):
        x,y = stats_a.get(key),stats_b.get(key)
        if isinstance(x,(int,float)) and not isinstance(x,bool) and isinstance(y,(int,float)):
            delta = y-x
            if not math.isclose(x,y,rel_tol=1e-6,abs_tol=1e-6):
                statistics_diff[key] = dict(python=x,rust=y,delta=delta)
        elif x != y: statistics_diff[key] = dict(python=x,rust=y)
    differences = collections.Counter()
    examples = collections.defaultdict(list)
    def walk(x,y,path):
        # Execution metadata is intentionally non-deterministic.
        if any(s in path for s in ('metadata','execution_time','timestamp','created_at')): return
        bucket = '.'.join(path.split('.')[:3])
        def record(kind):
            differences[kind] += 1
            if len(examples[kind])<12:
                examples[kind].append(dict(path=path,python=str(x)[:140],rust=str(y)[:140]))
        if isinstance(x,dict) and isinstance(y,dict):
            for key in sorted(x.keys()|y.keys()):
                if key not in x or key not in y:
                    differences['missing_fields'] += 1
                    if len(examples['missing_fields'])<20: examples['missing_fields'].append(path+'.'+key+(' (Rust missing)' if key not in y else ' (Python missing)'))
                else: walk(x[key],y[key],path+'.'+key)
        elif isinstance(x,list) and isinstance(y,list):
            if len(x)!=len(y): record('array_lengths')
            for i,(u,v) in enumerate(zip(x,y)): walk(u,v,path+f'[{i}]')
        elif isinstance(x,(float,int)) and not isinstance(x,bool) and isinstance(y,(float,int)) and not isinstance(y,bool):
            if not math.isclose(x,y,rel_tol=1e-6,abs_tol=1e-6): record('numbers')
        elif x != y: record('values')
    walk(a,b,'data')
    if python['status'] != 200 or rust['status'] != 200:
        walk(python.get('body'),rust.get('body'),'error')
    def curve_delta(field):
        ca,cb=a.get(field,{}),b.get(field,{})
        if not isinstance(ca,dict) or not isinstance(cb,dict): return None
        common=ca.keys()&cb.keys()
        diffs=[abs(ca[k]-cb[k]) for k in common if isinstance(ca[k],(int,float)) and isinstance(cb[k],(int,float))]
        return dict(python_points=len(ca),rust_points=len(cb),max_abs=max(diffs,default=0),missing_dates=len(ca.keys()^cb.keys()))
    return dict(status_match=python['status']==rust['status'],python_status=python['status'],rust_status=rust['status'],
                statistics=statistics_diff,python_final=stats_a.get('Final_Value'),rust_final=stats_b.get('Final_Value'),
                equity=curve_delta('equity_curve'),daily_returns=curve_delta('daily_returns'),
                differences=dict(differences),examples=dict(examples),
                python_supplemental=a.get('supplemental_status'),rust_supplemental=b.get('supplemental_status'))

def normal_cases():
    cases = [make('usd_single'),
        make('usd_five_8years',[dict(symbol=s,amount=10000) for s in ['AAPL','MSFT','SPY','QQQ','TLT']],start_date='2017-01-03',end_date='2024-12-31'),
        make('mixed_us_kr_cash',[dict(symbol='AAPL',amount=10000),dict(symbol='005930.KS',amount=10000),dict(symbol='현금',amount=5000,asset_type='cash')]),
        make('crypto_7day',[dict(symbol='BTC-USD',amount=10000),dict(symbol='ETH-USD',amount=10000)],start_date='2023-01-02',end_date='2023-12-31'),
        make('japan_europe_fx',[dict(symbol='7203.T',amount=10000),dict(symbol='SAP.DE',amount=10000)]),
        make('cash_only',[dict(symbol='현금',amount=10000,asset_type='cash'),dict(symbol='예금',amount=3000,asset_type='cash')]),
        make('zero_weight',[dict(symbol='AAPL',weight=100),dict(symbol='MSFT',weight=0)]),
        make('weights_cash',[dict(symbol='AAPL',weight=60),dict(symbol='MSFT',weight=30),dict(symbol='현금',weight=10,asset_type='cash')])]
    for frequency in ['weekly_1','weekly_2','monthly_1','monthly_2','monthly_3','monthly_6','monthly_12']:
        cases.append(make('dca_'+frequency,[dict(symbol='AAPL',amount=500,investment_type='dca',dca_frequency=frequency)],start_date='2020-01-02',end_date='2024-12-31'))
    for frequency in ['weekly_1','monthly_1','monthly_12']:
        cases.append(make('rebalance_'+frequency,[dict(symbol='AAPL',amount=10000),dict(symbol='MSFT',amount=8000),dict(symbol='현금',amount=2000,asset_type='cash')],rebalance_frequency=frequency,start_date='2020-01-02',end_date='2024-12-31'))
    cases.append(make('dca_with_rebalance',[dict(symbol='AAPL',amount=500,investment_type='dca',dca_frequency='weekly_2'),dict(symbol='MSFT',amount=5000),dict(symbol='현금',amount=1000,asset_type='cash')],rebalance_frequency='monthly_1',start_date='2020-01-02',end_date='2024-12-31'))
    strategies=[('sma',{'short_window':5,'long_window':15}),('ema',{'fast_window':5,'slow_window':12}),('rsi',{'rsi_period':7}),('bollinger',{'period':10,'std_dev':1.5}),('macd',{'fast_period':5,'slow_period':12,'signal_period':4})]
    for strategy,params in strategies:
        for suffix,parameters in [('default',{}),('custom',params)]:
            cases.append(make(strategy+'_'+suffix,[dict(symbol='AAPL',amount=10000),dict(symbol='MSFT',amount=10000)],strategy=strategy+'_strategy',strategy_params=parameters,start_date='2020-01-02',end_date='2024-12-31'))
    cases += [make('small_cash_no_trades',strategy='sma_strategy',portfolio=[dict(symbol='AAPL',amount=1)]),
              make('crypto_sma',[dict(symbol='BTC-USD',amount=10000)],strategy='sma_strategy',start_date='2023-01-02',end_date='2023-12-31'),
              make('krw_sma',[dict(symbol='005930.KS',amount=10000)],strategy='sma_strategy'),
              make('post_all_supplemental',include_stock_data=True,include_volatility_events=True,include_exchange_rates=True,include_benchmarks=True,include_news=True)]
    for name,path in [('prices','prices?symbols=AAPL&symbols=005930.KS&start_date=2023-01-03&end_date=2023-10-31'),('exchange','exchange-rates?start_date=2023-01-03&end_date=2023-10-31'),('benchmarks','benchmarks?start_date=2023-01-03&end_date=2023-10-31'),('news','news?symbols=AAPL&symbols=005930.KS&limit=15')]:
        cases.append(dict(name='get_'+name,method='GET',path='/api/v1/'+path))
    return cases

def boundary_cases():
    cases = [make('empty_portfolio',[]),make('duplicate_stock',[dict(symbol='AAPL',amount=1000),dict(symbol='AAPL',amount=2000)]),
        make('negative_amount',[dict(symbol='AAPL',amount=-1)]),make('zero_amount',[dict(symbol='AAPL',amount=0)]),
        make('amount_and_weight',[dict(symbol='AAPL',amount=1000,weight=100)]),make('missing_amount',[dict(symbol='AAPL')]),
        make('string_amount',[dict(symbol='AAPL',amount='10000')]),make('boolean_amount',[dict(symbol='AAPL',amount=True)]),
        make('invalid_symbol',[dict(symbol='AAPL<script>',amount=1000)]),make('cash_symbol_without_type',[dict(symbol='CASH',amount=1000)]),
        make('invalid_strategy',strategy='unknown'),make('invalid_params',strategy='sma_strategy',strategy_params={'short_window':30,'long_window':20}),
        make('invalid_commission',commission=.1),make('29_day_period',end_date='2023-02-01'),make('30_day_period',end_date='2023-02-02'),
        make('reverse_dates',end_date='2022-01-01'),make('future_dates',end_date='2099-01-01'),make('over_10years',start_date='2010-01-01'),
        make('malformed_date',start_date='not-a-date'),make('unknown_dca',portfolio=[dict(symbol='AAPL',amount=1000,investment_type='dca',dca_frequency='weekly_4')]),
        make('technical_dca',portfolio=[dict(symbol='AAPL',amount=1000,investment_type='dca')],strategy='sma_strategy'),
        make('technical_rebalance',strategy='sma_strategy',rebalance_frequency='monthly_1'),
        make('pre_ipo',portfolio=[dict(symbol='RIVN',amount=10000)],start_date='2020-01-02',end_date='2023-10-31'),
        make('unavailable_symbol',portfolio=[dict(symbol='ZZQQZZ9',amount=1000)]),
        make('partial_unavailable',portfolio=[dict(symbol='AAPL',amount=10000),dict(symbol='ZZQQZZ9',amount=1000)]),
        make('null_rebalance',rebalance_frequency=None),make('null_strategy_params',strategy_params=None)]
    omitted=make('omitted_technical_rebalance',strategy='sma_strategy');omitted['body'].pop('rebalance_frequency');cases.append(omitted)
    too_many=make('21_items',[dict(symbol='CASH'+str(i),amount=100,asset_type='cash') for i in range(21)]);cases.append(too_many)
    cases += [dict(name='get_unknown_argument',method='GET',path='/api/v1/prices?symbols=AAPL&start_date=2023-01-03&end_date=2023-10-31&extra=1'),
        dict(name='get_duplicate_date',method='GET',path='/api/v1/prices?symbols=AAPL&start_date=2023-01-03&start_date=2023-01-04&end_date=2023-10-31'),
        dict(name='get_missing_date',method='GET',path='/api/v1/prices?symbols=AAPL'),
        dict(name='get_invalid_news_limit',method='GET',path='/api/v1/news?symbols=AAPL&limit=50'),
        dict(name='invalid_json',method='POST',path='/api/v1/backtest',raw=b'{not json}'),
        dict(name='wrong_method',method='GET',path='/api/v1/backtest')]
    return cases

def run_cases(cases, phase, repeats):
    rows=[]
    for index,case in enumerate(cases):
        directory=OUT/phase/case['name'];directory.mkdir(parents=True,exist_ok=True)
        serializable={k:v for k,v in case.items() if k!='raw'}
        if 'raw' in case: serializable['raw']=case['raw'].decode()
        (directory/'input.json').write_text(json.dumps(serializable,ensure_ascii=False,indent=2))
        measurements={s:[] for s in SERVERS}
        latest={}
        first={}
        for iteration in range(repeats+1):
            order=list(SERVERS) if (iteration+index)%2==0 else list(reversed(SERVERS))
            for server in order:
                result=call(server,case)
                measurements[server].append({k:v for k,v in result.items() if k!='body'})
                latest[server]=result
                if iteration==0:
                    first[server]=result
                    (directory/(server+'-first.json')).write_text(json.dumps(result,ensure_ascii=False))
            # Transport or HTTP failures are behavior observations, not performance samples.
            if any(v['status']!=200 for v in latest.values()): break
        for server,result in latest.items():
            (directory/(server+'-last.json')).write_text(json.dumps(result,ensure_ascii=False))
        row=dict(name=case['name'],measurements=measurements,comparison=compare(latest['python'],latest['rust']))
        for server in SERVERS:
            samples=[v['ms'] for v in measurements[server][1:] if v['status']==200]
            row[server]=dict(first_ms=measurements[server][0]['ms'],median_ms=statistics.median(samples) if samples else None,min_ms=min(samples,default=None),max_ms=max(samples,default=None),samples=len(samples),status=latest[server]['status'],response_bytes=latest[server]['bytes'])
        if row['rust']['median_ms'] and row['python']['median_ms']:
            row['median_speedup']=row['python']['median_ms']/row['rust']['median_ms']
        rows.append(row)
        (OUT/(phase+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2))
        print(json.dumps(dict(phase=phase,name=case['name'],python=row['python'],rust=row['rust'],stats_diff=list(row['comparison']['statistics']),status_match=row['comparison']['status_match']),ensure_ascii=False),flush=True)
    return rows

def run_concurrency():
    case=make('concurrency',[dict(symbol=s,amount=10000) for s in ['AAPL','MSFT','SPY','QQQ','TLT']],start_date='2017-01-03',end_date='2024-12-31')
    rows=[]
    for server in SERVERS:
        call(server,case)
        for clients in ['same_client','distinct_clients']:
            for count in [1,2,8,16]:
                barrier=threading.Barrier(count)
                def work(index):
                    headers={'X-Forwarded-For':f'203.0.113.{index+1}' if clients=='distinct_clients' else '203.0.113.200'}
                    barrier.wait()
                    return call(server,case,headers)
                start=time.perf_counter()
                with concurrent.futures.ThreadPoolExecutor(max_workers=count) as pool:
                    results=list(pool.map(work,range(count)))
                total=time.perf_counter()-start
                good=[r['ms'] for r in results if r['status']==200]
                row=dict(server=server,clients=clients,requests=count,statuses=dict(collections.Counter(r['status'] for r in results)),wall_ms=total*1000,
                         successful_rps=len(good)/total,success_median_ms=statistics.median(good) if good else None,success_max_ms=max(good,default=None),
                         retry_after=sorted(set(r.get('retry_after') for r in results if r['status']==429)),error_bodies=[r['body'] for r in results if r['status']!=200],responses=[{k:v for k,v in r.items() if k!='body'} for r in results])
                rows.append(row);(OUT/'concurrent.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
                print(json.dumps(row,ensure_ascii=False),flush=True)
    return rows

(OUT/'metadata.json').write_text(json.dumps(dict(started=datetime.now(timezone.utc).isoformat(),servers=SERVERS,warm_repeats=5,method='Sequential alternating server order; first observation then 5 repeats. Existing caches are not cleared. Timings include HTTP transfer, exclude client JSON decoding.'),indent=2))
if args.phase in ('all','normal'): run_cases(normal_cases(),'normal',5)
if args.phase in ('all','boundary'): run_cases(boundary_cases(),'boundary',0)
if args.phase in ('all','concurrent'): run_concurrency()
