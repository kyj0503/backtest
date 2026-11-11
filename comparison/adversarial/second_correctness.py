"""Re-run preserved adversarial inputs and arithmetic against the second fix."""
import copy
import json
import math
from pathlib import Path
import shutil
import sys
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'.comparison/reports/second-corrected-2026-11-11'
read=lambda name:json.loads((REPORT/name).read_text(encoding='utf8'))
write=lambda name,value:(REPORT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')

def prepare():
    REPORT.mkdir(exist_ok=True,parents=True)
    prior=ROOT/'.comparison/reports/readversarial-2026-11-11'
    shutil.copyfile(prior/'cases.json',REPORT/'cases.json')
    (REPORT/'baseline').mkdir(exist_ok=True)
    shutil.copyfile(prior/'baseline/cases.json',REPORT/'baseline/cases.json')
    crate=ROOT/'.comparison/second-correctness-crate';crate.mkdir(exist_ok=True)
    for name in ['src','tests']:
        shutil.copytree(ROOT/'backtest_be_rust'/name,crate/name,dirs_exist_ok=True,copy_function=shutil.copy)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:
        shutil.copyfile(ROOT/'backtest_be_rust'/name,crate/name)
    (crate/'examples').mkdir(exist_ok=True)
    shutil.copyfile(Path(__file__).with_name('runner.rs'),crate/'examples/verify.rs')
    # Extract both chart callbacks from current source. No copied chart algorithm.
    js=Path(__file__).with_name('readversarial-frontend.cjs').read_text(encoding='utf8')
    js=js.replace('let weightExpression;','let weightExpression, symbolsExpression;')
    js=js.replace('ts.forEachChild(n,weightVisit);',"if(ts.isVariableDeclaration(n)&&ts.isIdentifier(n.name)&&n.name.text==='symbols')symbolsExpression=printer.printNode(ts.EmitHint.Expression,n.initializer.arguments[0],weightTree);\n  ts.forEachChild(n,weightVisit);")
    js=js.replace('const symbols=Array.from(new Set(cashOutcome.portfolio_composition.map(a=>a.symbol)));',"const portfolioComposition=cashOutcome.portfolio_composition;\nconst symbols=eval(transpile('('+symbolsExpression+')'))();")
    (REPORT/'frontend-probe.cjs').write_text(js,encoding='utf8')
    print('Prepared isolated current sources, 16 adversarial + 133 baseline inputs')

def http_prepare():
    prior=ROOT/'.comparison/reports/readversarial-2026-11-11'
    cases=json.loads((prior/'http-cases.json').read_text())
    fixtures=json.loads((prior/'http-fixtures.json').read_text())
    frontend=read('frontend-results.json')
    for name,key in [('fe_added_budget','addStock'),('fe_removed_budget','removeStock')]:
        c=next(c for c in cases if c['name']==name)
        c['request']['portfolio']=[{'symbol':'ZFE'+a['symbol'],'amount':a['amount'],'total_amount':a['totalAmount']} for a in frontend[key]['portfolio']]
    write('http-cases.json',cases);write('http-fixtures.json',fixtures)

def http_run():
    results=[]
    for c in read('http-cases.json'):
        req=urllib.request.Request('http://127.0.0.1:8002/api/v1/backtest',data=json.dumps(c['request']).encode(),headers={'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=45) as r:status=r.status;out=json.load(r)
        except urllib.error.HTTPError as e:status=e.code;out=json.loads(e.read())
        results.append({'name':c['name'],'status':status,'output':out})
        expected=422 if c['name'] in ['finite_annual_overflow','fe_added_budget'] else 200
        assert status==expected,(c['name'],status,out)
        print(c['name'],status,out.get('data',{}).get('portfolio_statistics',{}).get('Final_Value'))
    write('http-results.json',results)

def evaluate():
    out={x['name']:x['output'] for x in read('engine-results.json')}
    d=lambda name:out[name]['data']
    checks=[]
    def check(name,actual,expected):
        ok=math.isclose(actual,expected,rel_tol=1e-10,abs_tol=1e-7) if isinstance(actual,(int,float)) and isinstance(expected,(int,float)) else actual==expected
        checks.append({'name':name,'actual':actual,'expected':expected,'passed':ok})
    check('R01_pending_holiday_final',d('sunday_rebalance_weekly_1')['portfolio_statistics']['Final_Value'],17356.30580357143)
    check('R01_five_actual_rebalances',len(d('sunday_rebalance_weekly_1')['rebalance_history']),5)
    check('R01_other_market_holiday',d('one_market_holiday_True')['rebalance_history'][0]['date'],'2023-01-10')
    check('R02_fx_mark',d('fx_open_position_2000')['portfolio_statistics']['Final_Value'],5298.507)
    check('R02_cash_stays_USD',d('fx_open_position_2000')['strategy_details']['TEST']['cash'],597.014)
    check('R02_no_fx_change_control',d('fx_open_position_1000')['portfolio_statistics']['Final_Value'],10000)
    check('R02_buyhold_control',d('fx_buyhold_control_2000')['portfolio_statistics']['Final_Value'],4850)
    check('R03_no_invalid_snapshot',read('cache-race.json')['invalid_histories'],0)
    f=read('frontend-results.json')
    check('R04_added_asset_budget',f['addStock']['total'],10000)
    check('R04_missing_weight_blocked',len(f['addStock']['validation'])>0,True)
    check('R04_removed_asset_budget',f['removeStock']['total'],10000)
    check('R04_remaining_weight_valid',f['removeStock']['validation'],[])
    for key in ['strategy_details','portfolio_statistics']:
        actual=d('profit_factor')[key]['TEST']['profit_factor'] if key=='strategy_details' else d('profit_factor')[key]['Profit_Factor']
        check('R05_'+key,actual,3540/3660)
    check('R05_cash_reconciles',d('profit_factor')['portfolio_statistics']['Final_Value'],9880)
    check('R06_cash_chart',f['cashWeights']['rendered']['CASH__cash_1'],50)
    check('R06_stock_chart',f['cashWeights']['rendered']['TEST'],50)
    check('R07_buy_marker',f['openPosition']['buyMarkers'],1)
    check('R07_buy_count',f['openPosition']['chartCounts']['buys'],1)
    check('R07_no_fake_sell',f['openPosition']['chartCounts']['sells'],0)
    allocations=[{a['symbol']:a['amount'] for a in p} for p in f['orderPermutation']]
    check('R08_order_invariant',allocations[0],allocations[1])
    check('R08_normalized_allocation',allocations[0],{'A':9047.62,'B':952.38})
    check('R09_two_real_payments',d('monthly_2_calendar')['portfolio_statistics']['Initial_Value'],20000)
    check('R09_same_frontend_calendar',f['monthly2Periods'],2)
    check('R10_extreme_annual_error',out['finite_annual_overflow'].get('error_code'),422)
    check('R10_short_listing_full_calendar',d('finite_short_listing_overflow')['portfolio_statistics']['Final_Value'],96000688)
    check('R11_date_remains_string',d('cash_date_key')['weight_history'][0]['date'],'2023-01-02')
    http={c['name']:c for c in read('http-results.json')}
    for name in ['sunday_rebalance_weekly_1','fx_open_position_2000','profit_factor','monthly_2_calendar','finite_short_listing_overflow']:
        check('HTTP_'+name,http[name]['output']['data']['portfolio_statistics']['Final_Value'],d(name)['portfolio_statistics']['Final_Value'])
    check('HTTP_R04_added_zero_weight_rejected',http['fe_added_budget']['status'],422)
    check('HTTP_R04_removed_budget',http['fe_removed_budget']['output']['data']['portfolio_statistics']['Initial_Value'],10000)
    result={'checks':len(checks),'passed':sum(c['passed'] for c in checks),'failed':sum(not c['passed'] for c in checks),'detail':checks}
    write('second-checks.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='detail'}))
    for c in checks:
        if not c['passed']:print(c)
    assert result['failed']==0

if __name__=='__main__':
    {'prepare':prepare,'http-prepare':http_prepare,'http':http_run,'evaluate':evaluate}[sys.argv[1]]()
