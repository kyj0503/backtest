"""Independent follow-up audit. Creates evidence copies, never edits the service."""
import copy
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import shutil
import sys
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'.comparison/reports/third-audit-2026-11-11'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')

def prepare():
    REPORT.mkdir(parents=True,exist_ok=True)
    old=read(ROOT/'comparison/adversarial/second-corrected-evidence-2026-11-11.json')
    assert all(hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()==h for p,h in old['source_sha256'].items())
    write(REPORT/'source-sha256.json',old['source_sha256'])
    crate=ROOT/'.comparison/third-audit-crate';crate.mkdir(exist_ok=True)
    for name in ['src','tests']:
        shutil.copytree(ROOT/'backtest_be_rust'/name,crate/name,dirs_exist_ok=True,copy_function=shutil.copy)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:
        shutil.copyfile(ROOT/'backtest_be_rust'/name,crate/name)
    (crate/'examples').mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).with_name('runner.rs'),crate/'examples/verify.rs')
    for name,source in [('baseline','baseline/cases.json'),('previous','cases.json')]:
        (REPORT/name).mkdir(exist_ok=True)
        shutil.copyfile(ROOT/'.comparison/reports/second-corrected-2026-11-11'/source,REPORT/name/'cases.json')
    cases=[]
    start=date(2023,1,2);end=start+timedelta(days=39)
    def hist(symbol,prices,opens=None,dates=None,currency='USD'):
        if dates is None:dates=[start+timedelta(days=i) for i in range(len(prices))]
        return {'symbol':symbol,'currency':currency,'company_name':symbol,'exchange':'synthetic','first_trade_date':None,
          'bars':[{'date':str(d),'open':o,'high':max(o,p),'low':min(o,p),'close':p,'volume':1000} for d,p,o in zip(dates,prices,opens or prices)]}
    def request(portfolio=None,**kwargs):
        return {'portfolio':portfolio or [{'symbol':'TEST','amount':10000}], 'start_date':str(start),'end_date':str(end),'commission':0,'rebalance_frequency':'none',**kwargs}
    def add(name,r,h):cases.append({'name':name,'request':r,'histories':h})
    flat=hist('TEST',[100]*40)
    add('initial_fee',request(commission=.01),{'TEST':flat})
    weekend=request(start_date='2023-01-01')
    add('weekend_cash_weights',weekend,{'TEST':flat})
    # Only an adjusted price unit changes; original raw quote economic history is the same.
    for factor in [1,.5]:
        prices=[1000,990,980,970]+[1500]*36
        h=hist('TEST',[p*factor for p in prices])
        r=request(strategy='rsi_strategy',strategy_params={'rsi_period':2})
        add('split_unit_'+str(factor),r,{'TEST':h})
        add('split_fractional_control_'+str(factor),request(),{'TEST':h})
    for n in [40,400,800]:
        prices=[100,120]+[120]*(n-2)
        add('front_loaded_gain_'+str(n),request(end_date=str(start+timedelta(days=n-1))),{'TEST':hist('TEST',prices)})
    monthly_start=date(2020,1,2);n=2000
    add('front_loaded_gain_monthly',request(start_date=str(monthly_start),end_date=str(monthly_start+timedelta(days=n-1))),
        {'TEST':hist('TEST',[100,120]+[120]*(n-2),dates=[monthly_start+timedelta(days=i) for i in range(n)])})
    # Controlled gap: buy signal on day 3, next open 97 versus closing price 110.
    prices=[100,99,98,110]+[110]*36
    opens=prices.copy();opens[3]=97
    add('open_close_gap',request(strategy='rsi_strategy',strategy_params={'rsi_period':2}),{'TEST':hist('TEST',prices,opens)})
    # Open holding exactly at 1/4 while price sampling keeps 1/2 and 1/9.
    for sign in [1,-1]:
        n=800;prices=[100,99,98,97]+[97]*(n-4)
        prices[5]=97+sign*2
        add('weekly_trade_'+str(sign),request(end_date=str(start+timedelta(days=n-1)),strategy='rsi_strategy',strategy_params={'rsi_period':2}),{'TEST':hist('TEST',prices)})
    prices=[100]*8+[99]+[98]*791
    add('weekly_backdated_open',request(end_date=str(start+timedelta(days=799)),strategy='rsi_strategy',strategy_params={'rsi_period':2}),{'TEST':hist('TEST',prices)})
    # Historical asset that does not start trading until later; cash is still held meanwhile.
    late=hist('LATE',[100]*30,dates=[start+timedelta(days=i) for i in range(10,40)])
    add('late_initial_weights',request([{'symbol':'TEST','amount':5000},{'symbol':'LATE','amount':5000}]),{'TEST':flat,'LATE':late})
    rebalance=copy.deepcopy(next(c for c in read(ROOT/'.comparison/reports/readversarial-2026-11-11/cases.json') if c['name']=='sunday_rebalance_weekly_1'))
    rebalance['name']='rebalance_csv_fees';rebalance['request']['commission']=.01;cases.append(rebalance)
    write(REPORT/'cases.json',cases)
    http_cases=[];fixtures={}
    for i,c in enumerate(cases):
        req=copy.deepcopy(c['request']);mapping={symbol:f'ZT{i:02}{j}' for j,symbol in enumerate(c['histories'])}
        for asset in req['portfolio']:asset['symbol']=mapping[asset['symbol']]
        for symbol,h in c['histories'].items():
            new=copy.deepcopy(h);new['symbol']=mapping[symbol];fixtures[new['symbol']]=new
        for k in ['stock_data','volatility_events','exchange_rates','benchmarks','news']:req['include_'+k]=False
        http_cases.append({'name':c['name'],'request':req,'symbol_mapping':mapping})
    write(REPORT/'http-cases.json',http_cases);write(REPORT/'http-fixtures.json',fixtures)
    print('Source manifest unchanged:',len(old['source_sha256']),'New cases:',len(cases))

def prepare_before():
    before=ROOT/'.comparison/third-audit-before-crate';before.mkdir(exist_ok=True)
    source=ROOT/'.comparison/readversarial-crate'
    expected=read(ROOT/'comparison/adversarial/readversarial-evidence-2026-11-11.json')['source_sha256']
    for key,digest in expected.items():
        p=source/'src'/Path(key).name
        assert hashlib.sha256(p.read_bytes()).hexdigest()==digest, key
    for name in ['src','tests']:
        shutil.copytree(source/name,before/name,dirs_exist_ok=True,copy_function=shutil.copy)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:
        shutil.copyfile(source/name,before/name)
    (before/'examples').mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).with_name('runner.rs'),before/'examples/verify.rs')
    (REPORT/'before').mkdir(exist_ok=True)
    shutil.copyfile(REPORT/'cases.json',REPORT/'before/cases.json')
    print('Verified pre-R01-R11 source hashes; before-control prepared')

def inspect():
    cases=read(REPORT/'engine-results.json')
    for c in cases:
        d=c['output'].get('data',{})
        s=d.get('portfolio_statistics',{})
        daily=d.get('daily_returns',{})
        growth=1
        for r in daily.values():growth*=1+r/100
        weights=d.get('weight_history',[{}])[0]
        print(c['name'],json.dumps({'final':s.get('Final_Value'),'TWR':s.get('Time_Weighted_Return'),'daily_compound':(growth-1)*100,'first_weights':weights,'volatility':s.get('Annual_Volatility'),'error':c['output'].get('error')},ensure_ascii=False))

def http():
    outputs=[]
    for c in read(REPORT/'http-cases.json'):
        req=urllib.request.Request('http://127.0.0.1:8002/api/v1/backtest',data=json.dumps(c['request']).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:status=r.status;output=json.load(r)
        except urllib.error.HTTPError as e:status=e.code;output=json.loads(e.read())
        outputs.append({'name':c['name'],'status':status,'output':output})
        print(c['name'],status,output.get('data',{}).get('portfolio_statistics',{}).get('Final_Value'))
    write(REPORT/'http-results.json',outputs)

if __name__=='__main__':{'prepare':prepare,'inspect':inspect,'http':http,'before':prepare_before}[sys.argv[1]]()
