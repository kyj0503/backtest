"""Adversarial probes after S01-S06. Pure arithmetic oracles, no Python service."""
import copy
from datetime import date, timedelta
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / '.comparison/reports/fourth-audit-2026-11-11'
START = date(2023, 1, 2)


def history(prices, opens=None, symbol='TEST', currency='USD'):
    return dict(symbol=symbol, currency=currency, company_name=symbol, exchange='synthetic', first_trade_date=None,
        bars=[dict(date=str(START+timedelta(days=i)), open=o, high=max(p,o), low=min(p,o), close=p, volume=1000)
              for i,(p,o) in enumerate(zip(prices, opens or prices))])


def prepare():
    cases=[]
    def add(name, prices, extra=None, opens=None, histories=None, oracle=None):
        request=dict(portfolio=[dict(symbol='TEST',amount=10000)], start_date=str(START),
            end_date=str(START+timedelta(days=len(prices)-1)), commission=0,rebalance_frequency='none')
        request.update(extra or {})
        cases.append(dict(name=name,request=request,histories=histories or {'TEST':history(prices,opens)},oracle=oracle))
    for period in [5,20]:
        for fee in [0,.01]:
            p=[100.]*40;p[period-1]=80.;o=p.copy();o[period]=80.
            q=9500/(80*(1+fee))
            add(f'first_valid_bollinger_{period}_{fee}',p,
                dict(strategy='bollinger_strategy',strategy_params=dict(period=period,std_dev=1),commission=fee),o,
                oracle=dict(final=10000-q*80*(1+fee)+q*100*(1-fee),entry=str(START+timedelta(days=period))))
            # Move the exact same dip one bar later, after the skipped valid bar.
            p=[100.]*40;p[period]=80.;o=p.copy();o[period+1]=80.
            add(f'next_valid_bollinger_{period}_{fee}',p,
                dict(strategy='bollinger_strategy',strategy_params=dict(period=period,std_dev=1),commission=fee),o,
                oracle=dict(final=10000-q*80*(1+fee)+q*100*(1-fee)))
    p=[110.]*10+[100.]*10+[110.]*10+[150.]*10
    add('sma_negative_equal_positive',p,dict(strategy='sma_strategy',strategy_params=dict(short_window=2,long_window=10)),
        oracle=dict(final=10000+(9500/110)*(150-110),entry='2023-01-23'))
    p=[100.]*20+[110.]*10+[150.]*10
    add('ema_equal_positive',p,dict(strategy='ema_strategy',strategy_params=dict(fast_window=5,slow_window=10)),
        oracle=dict(final=10000+(9500/110)*(150-110),entry='2023-01-23'))
    p=[100.]*20+[110.]*20
    add('macd_equal_positive',p,dict(strategy='macd_strategy',strategy_params=dict(fast_period=5,slow_period=10,signal_period=2),commission=.01))
    p=[100.]*10+[200.]*30
    for strategy,params in [('sma_strategy',dict(short_window=2,long_window=20)),('rsi_strategy',dict(rsi_period=2))]:
        add('buy_hold_reference_'+strategy,p,dict(strategy=strategy,strategy_params=params),oracle=dict(buy_hold_return=100.))
    # Rebalance and money-flow invariants, including non-coincident DCA schedules.
    for seed in range(20):
        n=100
        a=[80+((i*17+seed*11)%53) for i in range(n)]
        b=[120+((i*13+seed*7)%37) for i in range(n)]
        add(f'ledger_{seed}',a,dict(commission=.01,rebalance_frequency=['weekly_1','monthly_1'][seed%2],
            portfolio=[dict(symbol='A',amount=1000,investment_type='dca',dca_frequency='monthly_1'),dict(symbol='B',amount=1000),dict(symbol='USD',amount=500,asset_type='cash')]),
            histories={'A':history(a,symbol='A'),'B':history(b,symbol='B')})
    # The 95% signal budget is invariant under powers-of-two price unit changes.
    p=[100,99,98,97]+[150]*36
    for exponent in [-12,-4,0,4,12]:
        scale=2.**exponent
        add(f'unit_scale_{exponent}',[v*scale for v in p],dict(strategy='rsi_strategy',strategy_params=dict(rsi_period=2),commission=.01),
            oracle=dict(final=10000-9500/(98*1.01)*97*1.01+9500/(98*1.01)*150*.99))
    late=history([100.]*40,symbol='LATE');late['bars']=late['bars'][10:];late['first_trade_date']=str(START+timedelta(days=10))
    add('late_listing_cash', [100.]*40,dict(portfolio=[dict(symbol='LATE',amount=10000)]),histories={'LATE':late},oracle=dict(final=10000))
    high=[1_000_000.]*7+[2_000_000.]*33
    add('fractional_csv_quantity',high,dict(portfolio=[dict(symbol='HIGH',amount=100),dict(symbol='USD',amount=100,asset_type='cash')],rebalance_frequency='weekly_1'),histories={'HIGH':history(high,symbol='HIGH')},oracle=dict(final=300))
    (OUT/'cases.json').write_text(json.dumps(cases),encoding='utf8')
    http=[];fixtures={}
    for i,c in enumerate(cases):
        mapping={s:f'QA{i:02}{j}' for j,s in enumerate(c['histories'])}
        req=copy.deepcopy(c['request'])
        for a in req['portfolio']:
            if a.get('asset_type')!='cash':a['symbol']=mapping[a['symbol']]
        for s,h in c['histories'].items():
            new=copy.deepcopy(h);new['symbol']=mapping[s];fixtures[new['symbol']]=new
        req.update({'include_'+k:False for k in ['stock_data','volatility_events','exchange_rates','benchmarks','news']})
        http.append(dict(name=c['name'],request=req,mapping=mapping))
    (OUT/'http-cases.json').write_text(json.dumps(http),encoding='utf8')
    (OUT/'http-fixtures.json').write_text(json.dumps(fixtures),encoding='utf8')
    print('Prepared',len(cases),'new input scenarios')


def evaluate():
    outputs={c['name']:c['output'] for c in json.loads((OUT/'engine-results.json').read_text())}
    cases=json.loads((OUT/'cases.json').read_text());checks=[]
    def near(name,actual,expected):
        policy=name.startswith(('sma_negative_equal_positive/independent_final','ema_equal_positive/independent_final','buy_hold_reference_sma_strategy/same_period_buy_hold'))
        checks.append(dict(name=name,actual=actual,expected=expected,basis='policy-dependent' if policy else 'independent-invariant',passed=math.isclose(actual,expected,abs_tol=1e-7,rel_tol=1e-10)))
    for c in cases:
        name=c['name'];d=outputs[name]['data'];s=d['portfolio_statistics'];oracle=c['oracle'] or {}
        if 'final' in oracle:near(name+'/independent_final',s['Final_Value'],oracle['final'])
        if 'buy_hold_return' in oracle:near(name+'/same_period_buy_hold',d['strategy_details']['TEST']['buy_and_hold_return_pct'],oracle['buy_hold_return'])
        near(name+'/account_sum',sum(v['final_value'] for v in d['individual_returns'].values()),s['Final_Value'])
        near(name+'/public_twr',(math.prod(1+v/100 for v in d['daily_returns'].values())-1)*100,s['Time_Weighted_Return'])
        for row in d['weight_history']:
            near(name+'/weights/'+row['date'],sum(v for k,v in row.items() if k!='date'),1.)
        if name.startswith('ledger_'):
            near(name+'/profit_conservation',sum(v['return']/100*v['amount'] for v in d['individual_returns'].values()),s['Final_Value']-s['Initial_Value'])
            for event in d['rebalance_history']:
                near(name+'/commission/'+event['date'],event['commission_cost'],sum(t['commission'] for t in event['trades']))
                for t in event['trades']:
                    near(name+'/turnover_fee/'+event['date']+'/'+t['symbol'],t['commission'],t.get('shares',0)*t['price']*c['request']['commission'])
    result=dict(cases=len(cases),checks=len(checks),passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks),details=checks)
    result['confirmed_failures']=sum(not c['passed'] and c['basis']=='independent-invariant' for c in checks)
    result['policy_discrepancies']=sum(not c['passed'] and c['basis']=='policy-dependent' for c in checks)
    (OUT/'checks.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in result.items() if k!='details'}))
    for c in checks:
        if not c['passed']:print(json.dumps(c))


if __name__=='__main__':{'prepare':prepare,'evaluate':evaluate}[sys.argv[1]]()
