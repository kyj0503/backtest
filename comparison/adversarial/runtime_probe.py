"""Independent runtime checks against the isolated, fixture-only Rust API."""
import argparse
import copy
import json
import urllib.request
import urllib.error
from pathlib import Path


def prepare(directory):
    original=json.loads((directory/'cases.json').read_text(encoding='utf-8'))
    names=['last_close_future_buy','technical_roundtrip_fee','cash_dca','cash_symbol_collision',
           'rebalance_fee','rsi_wilder_seed','ui_weight_dca_budget','dca_growth','finite_input_overflow']
    selected=[]
    histories={}
    for i,case in enumerate(c for c in original if c['name'] in names):
        case=copy.deepcopy(case)
        for old,h in list(case['histories'].items()):
            symbol=old if old=='CASH' else f'Z{i}{old}'
            h['symbol']=symbol
            histories[symbol]=h
            for a in case['request']['portfolio']:
                if a['symbol']==old and a.get('asset_type')!='cash':
                    a['symbol']=symbol
        if case['name']=='dca_growth':
            case['request']['include_benchmarks']=True
            for sym in ['^GSPC','^IXIC']:
                h=copy.deepcopy(next(iter(case['histories'].values())))
                h['symbol']=sym
                histories[sym]=h
        selected.append({'name':case['name'],'request':case['request']})
    from audit import history
    histories['KRW=X']=history([1000]*40,'KRW=X')
    (directory/'http-fixtures.json').write_text(json.dumps(histories),encoding='utf-8')
    (directory/'http-cases.json').write_text(json.dumps(selected),encoding='utf-8')
    print(f'Prepared {len(selected)} HTTP financial scenarios')


def run(directory,url):
    results=[]
    def call(name,path,body=None):
        req=urllib.request.Request(url+path,data=None if body is None else json.dumps(body).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=30) as response:
                status=response.status
                value=json.load(response)
        except urllib.error.HTTPError as e:
            status=e.code
            raw=e.read().decode()
            try: value=json.loads(raw)
            except ValueError: value={'raw':raw}
        result={'name':name,'status':status,'output':value}
        results.append(result)
        return result
    selected=json.loads((directory/'http-cases.json').read_text(encoding='utf-8'))
    for case in selected:
        r=call(case['name'],'/api/v1/backtest',case['request'])
        print(case['name'],r['status'],r['output'].get('data',{}).get('portfolio_statistics',{}).get('Final_Value'))
    base=next(c['request'] for c in selected if c['name']=='last_close_future_buy')
    for name,updates in [('negative_fee',{'commission':-.1}),('future_date',{'end_date':'2099-01-01'}),('bad_strategy',{'strategy':'unrecognized'}),('technical_dca',{'portfolio':[{'symbol':base['portfolio'][0]['symbol'],'amount':1000,'investment_type':'dca'}]}),('empty_portfolio',{'portfolio':[]})]:
        r=call(name,'/api/v1/backtest',{**base,**updates})
        assert r['status']==422,(name,r['status'])
    symbol=base['portfolio'][0]['symbol']
    query='?start_date=2023-01-02&end_date=2023-02-10'
    call('prices','/api/v1/prices'+query+'&symbols='+symbol)
    call('exchange','/api/v1/exchange-rates'+query)
    call('benchmarks','/api/v1/benchmarks'+query)
    call('news_empty','/api/v1/news?symbols='+symbol)
    call('liveness','/health')
    by_name={r['name']:r for r in results}
    def data(name):return by_name[name]['output']['data']
    assert all(r['status']==(422 if r['name'] in {'finite_input_overflow','negative_fee','future_date','bad_strategy','technical_dca','empty_portfolio'} else 200) for r in results)
    assert data('last_close_future_buy')['portfolio_statistics']['Final_Value']==10000
    assert data('technical_roundtrip_fee')['portfolio_statistics']['Final_Value']==9830
    assert next(iter(data('cash_dca')['equity_curve'].values()))==500
    assert sum(r['final_equity'] for r in data('cash_symbol_collision')['individual_results'])==5000
    assert data('ui_weight_dca_budget')['portfolio_statistics']['Initial_Value']==10000
    assert data('dca_growth')['portfolio_statistics']['Total_Return']==50
    assert data('dca_growth')['portfolio_statistics']['Time_Weighted_Return']==100
    assert data('dca_growth')['portfolio_statistics']['alpha_vs_sp500_pct']==0
    (directory/'http-results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'HTTP requests completed: {len(results)}; every status and independent financial assertions passed')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('mode',choices=['prepare','run'])
    p.add_argument('directory',type=Path)
    p.add_argument('--url',default='http://127.0.0.1:8002')
    a=p.parse_args()
    prepare(a.directory) if a.mode=='prepare' else run(a.directory,a.url)
