"""Second independent audit. Synthetic inputs, not Python-parity expectations."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import copy
import urllib.request
import urllib.error

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / '.comparison/reports/readversarial-2026-11-11'
CRATE = ROOT / '.comparison/readversarial-crate'
START = dt.date(2023, 1, 2)

def history(prices, symbol='TEST', currency='USD', start=START, weekdays=False, opens=None):
    return {'symbol': symbol, 'currency': currency, 'bars': [
        {'date': str(start+dt.timedelta(days=i)), 'open': (opens or prices)[i],
         'high': max(p, (opens or prices)[i]), 'low': min(p, (opens or prices)[i]),
         'close': p, 'volume': 1000000}
        for i,p in enumerate(prices) if not weekdays or (start+dt.timedelta(days=i)).weekday()<5]}

def asset(symbol='TEST', amount=10000, **kw):
    return {'symbol':symbol,'amount':amount,**kw}

def request(n=40,start=START,portfolio=None,**kw):
    return {'portfolio':portfolio or [asset()],'start_date':str(start),
            'end_date':str(start+dt.timedelta(days=n-1)), 'commission':0,
            'rebalance_frequency':'none','include_stock_data':False,
            'include_exchange_rates':False,'include_benchmarks':False,
            'include_news':False,'include_volatility_events':False,**kw}

def prepare():
    REPORT.mkdir(parents=True,exist_ok=True)
    CRATE.mkdir(parents=True,exist_ok=True)
    for name in ['src','tests']:
        shutil.copytree(ROOT/'backtest_be_rust'/name,CRATE/name,dirs_exist_ok=True)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:
        shutil.copy2(ROOT/'backtest_be_rust'/name,CRATE/name)
    (CRATE/'examples').mkdir(exist_ok=True)
    shutil.copy2(Path(__file__).with_name('runner.rs'),CRATE/'examples/readversarial.rs')
    cases=[]
    def add(name,req,*histories):
        cases.append({'name':name,'request':req,'histories':{h['symbol']:h for h in histories}})
    sunday=dt.date(2023,1,1)
    for mode in ['none','weekly_1']:
        add('sunday_rebalance_'+mode,request(n=43,start=sunday,portfolio=[asset('A',5000),asset('B',5000)],rebalance_frequency=mode),
            history([100+5*i for i in range(43)],'A',start=sunday,weekdays=True),history([100]*43,'B',start=sunday,weekdays=True))
    rsi={'strategy':'rsi_strategy','strategy_params':{'rsi_period':2,'rsi_oversold':40,'rsi_overbought':70}}
    declining=[100,99,98]+[97]*37
    foreign=history(declining[:-1],currency='KRW')
    for ending in [1000,2000]:
        add('fx_open_position_'+str(ending),request(**rsi),foreign,history([1000]*39+[ending],'KRW=X'))
        add('fx_buyhold_control_'+str(ending),request(),foreign,history([1000]*39+[ending],'KRW=X'))
    add('open_position',request(**rsi),history(declining))
    add('cash_date_key',request(portfolio=[asset('date',5000,asset_type='cash'),asset(amount=5000)],**rsi),history(declining))
    add('cash_weight_chart',request(portfolio=[asset('CASH',5000,asset_type='cash'),asset(amount=5000)]),history([100]*40))
    # Repeated profitable and losing round trips have different dollar capital bases.
    wave=[100]*4+[80]*4+[110]*4+[70]*4+[100]*24
    gap_opens=wave.copy()
    gap_opens[17]=50
    add('profit_factor',request(n=len(wave),**rsi),history(wave,opens=gap_opens))
    add('finite_annual_overflow',request(**rsi),history([100,99,98,97]+[1e50]*36))
    add('finite_short_listing_overflow',request(**rsi),history([100,99,98,1000000],start=dt.date(2023,2,7),opens=[100,99,98,97]))
    # Valid calendar dates include a second scheduled payment, but fewer than 60 days.
    add('monthly_2_calendar',request(n=59,start=dt.date(2023,1,30),portfolio=[asset(investment_type='dca',dca_frequency='monthly_2')]),
        history([100]*59,start=dt.date(2023,1,30)))
    add('monthly_2_60day_control',request(n=61,start=dt.date(2023,1,30),portfolio=[asset(investment_type='dca',dca_frequency='monthly_2')]),
        history([100]*61,start=dt.date(2023,1,30)))
    # Rebalancing a multi-market portfolio on a holiday for exactly one market.
    for holiday in [False,True]:
        a=history([100]*7+[200]*33,'A')
        if holiday: a['bars']=[b for b in a['bars'] if b['date']!='2023-01-09']
        add('one_market_holiday_'+str(holiday),request(portfolio=[asset('A',5000),asset('B',5000)],rebalance_frequency='weekly_1'),a,history([100]*40,'B'))
    (REPORT/'cases.json').write_text(json.dumps(cases),encoding='utf8')
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backtest_be_rust/src').rglob('*.rs')}
    (REPORT/'source-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf8')
    print(f'Prepared {len(cases)} fresh cases in {REPORT}')

def controls():
    baseline=REPORT/'baseline'
    baseline.mkdir(exist_ok=True)
    shutil.copy2(REPORT.parent/'corrected-2026-11-11/cases.json',baseline/'cases.json')
    before=REPORT/'before'
    before.mkdir(exist_ok=True)
    shutil.copy2(REPORT/'cases.json',before/'cases.json')
    prior=ROOT/'.comparison/readversarial-before-crate'
    prior.mkdir(exist_ok=True)
    for name in ['src','tests']:
        shutil.copytree(ROOT/'.comparison/adversarial-crate'/name,prior/name,dirs_exist_ok=True)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:
        shutil.copy2(ROOT/'.comparison/adversarial-crate'/name,prior/name)
    (prior/'examples').mkdir(exist_ok=True)
    shutil.copy2(Path(__file__).with_name('runner.rs'),prior/'examples/readversarial.rs')
    selected=[]; histories={}
    original=json.loads((REPORT/'cases.json').read_text())
    for i,c in enumerate(original):
        if c['name'].endswith('_1000'):continue
        c=copy.deepcopy(c)
        for old,h in c['histories'].items():
            symbol=old if old.endswith('=X') else f'Z{i}{old}'
            h['symbol']=symbol;histories[symbol]=h
            for a in c['request']['portfolio']:
                if a['symbol']==old and a.get('asset_type')!='cash':a['symbol']=symbol
        selected.append({'name':c['name'],'request':c['request']})
    front=json.loads((REPORT/'frontend-results.json').read_text())
    for name,obj in [('fe_added_budget',front['addStock']),('fe_removed_budget',front['removeStock'])]:
        portfolio=[]
        for a in obj['portfolio']:
            symbol='ZFE'+a['symbol']
            histories[symbol]=history([100]*40,symbol)
            item=asset(symbol,a['amount'])
            if 'totalAmount' in a:item['total_amount']=a['totalAmount']
            portfolio.append(item)
        selected.append({'name':name,'request':request(portfolio=portfolio)})
    (REPORT/'http-fixtures.json').write_text(json.dumps(histories),encoding='utf8')
    (REPORT/'http-cases.json').write_text(json.dumps(selected),encoding='utf8')
    print(f'Prepared {len(selected)} HTTP scenarios and before/baseline controls')

def http():
    results=[]
    for c in json.loads((REPORT/'http-cases.json').read_text()):
        req=urllib.request.Request('http://127.0.0.1:8002/api/v1/backtest',
            data=json.dumps(c['request']).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=30) as r:status=r.status;out=json.load(r)
        except urllib.error.HTTPError as e:
            status=e.code
            try:out=json.loads(e.read())
            except ValueError:out={'unparseable':True}
        results.append({'name':c['name'],'status':status,'output':out})
        print(c['name'],status,out.get('data',{}).get('portfolio_statistics',{}).get('Final_Value'))
    (REPORT/'http-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf8')

def summarize():
    results=json.loads((REPORT/'engine-results.json').read_text())
    compact=[]
    for case in results:
        out=case['output']; d=out.get('data',{}); details=d.get('strategy_details',{})
        item={'name':case['name'],'error':out.get('error'),'panic':out.get('panic'),
              'stats':d.get('portfolio_statistics'),'rebalance_dates':[x.get('date') for x in d.get('rebalance_history',[])],
              'positions':{s:v.get('open_positions') for s,v in details.items()},
              'details':{s:{k:v.get(k) for k in ['cash','profit_factor','trade_log','final_equity']} for s,v in details.items()}}
        if case['name']=='cash_date_key':item['weights_first']=d['weight_history'][0]
        compact.append(item)
    (REPORT/'compact-results.json').write_text(json.dumps(compact,indent=2),encoding='utf8')
    for x in compact:
        s=x['stats'] or {}
        print(x['name'], 'final=',s.get('Final_Value'),'error=',x['error'],'panic=',x['panic'], 'rebalances=',len(x['rebalance_dates']))

if __name__=='__main__':
    {'prepare':prepare,'summarize':summarize,'controls':controls,'http':http}[sys.argv[1]]()
