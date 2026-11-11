"""Summarize observed failures and independent arithmetic for the second audit."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'.comparison/reports/readversarial-2026-11-11'
read=lambda p:json.loads((REPORT/p).read_text(encoding='utf8'))
engine={c['name']:c['output'] for c in read('engine-results.json')}
before={c['name']:c['output'] for c in read('before/engine-results.json')}
http={c['name']:c for c in read('http-results.json')}
frontend=read('frontend-results.json')

# Independent two-asset, fee-free ledger: pending Sunday schedules fill at the
# next common trading close; no migrated/Python engine output is an oracle.
shares=[0.0,0.0]; cash=10000.0; pending=False; fills=[]
for i in range(43):
    day=dt.date(2023,1,1)+dt.timedelta(days=i)
    if i>0 and i%7==0:pending=True
    if day.weekday()>=5:continue
    prices=[100+5*i,100]
    if cash:
        shares=[5000/p for p in prices];cash=0
    if pending:
        total=sum(s*p for s,p in zip(shares,prices))
        shares=[total/2/p for p in prices]
        fills.append(str(day));pending=False
expected_rebalanced=sum(s*p for s,p in zip(shares,prices))

fx=engine['fx_open_position_2000']['data']['strategy_details']['TEST']
expected_fx=fx['cash']+fx['open_positions'][0]['Size']*97/2000
profit=engine['profit_factor']['data']['strategy_details']['TEST']
pnl=[t['PnL'] for t in profit['trade_log']]
expected_pf=sum(p for p in pnl if p>0)/-sum(p for p in pnl if p<0)
permuted=[{a['symbol']:a['amount'] for a in p} for p in frontend['orderPermutation']]

findings=[
 {'id':'R01','priority':'P1','kind':'regression','title':'휴장일 리밸런싱 일정 소실',
  'expected':{'rebalance_dates':fills,'final_value':expected_rebalanced},
  'actual':{'rebalance_count':len(engine['sunday_rebalance_weekly_1']['data']['rebalance_history']),
            'final_value':engine['sunday_rebalance_weekly_1']['data']['portfolio_statistics']['Final_Value']},
  'source':'backtest_be_rust/src/engine.rs:282'},
 {'id':'R02','priority':'P1','kind':'residual','title':'기술적 전략의 휴장일 FX 평가 누락',
  'expected':expected_fx,'actual':engine['fx_open_position_2000']['data']['portfolio_statistics']['Final_Value'],
  'cash':fx['cash'],'shares':fx['open_positions'][0]['Size'],'source':'backtest_be_rust/src/engine.rs:630'},
 {'id':'R03','priority':'P1','kind':'regression','title':'동시 갱신 시 메타데이터와 시세 스냅샷 불일치',
  'expected_invalid_hits':0,'actual':read('cache-race.json'),'source':'backtest_be_rust/src/data.rs:228'},
 {'id':'R04','priority':'P1','kind':'residual','title':'비중 모드 종목 추가/삭제 후 총 투자금 보존 실패',
  'expected':10000,'actual_added':frontend['addStock']['total'],'actual_removed':frontend['removeStock']['total'],
  'validation_added':frontend['addStock']['validation'],'validation_removed':frontend['removeStock']['validation'],
  'http_added_initial':http['fe_added_budget']['output']['data']['portfolio_statistics']['Initial_Value'],
  'source':'../backtest-console/src/features/backtest/model/backtestFormReducer.ts:40'},
 {'id':'R05','priority':'P2','kind':'residual','title':'손익 금액 대신 수익률을 더하는 Profit Factor',
  'trade_pnl':pnl,'expected':expected_pf,'actual':profit['profit_factor'],
  'actual_portfolio':engine['profit_factor']['data']['portfolio_statistics']['Profit_Factor'],
  'source':'backtest_be_rust/src/strategy.rs:329'},
 {'id':'R06','priority':'P2','kind':'regression','title':'현금 비중의 API/화면 식별자 불일치',
  'expected_cash_pct':50,'actual':frontend['cashWeights'],'source':'backtest_be_rust/src/engine.rs:435'},
 {'id':'R07','priority':'P2','kind':'regression','title':'미청산 진입 거래가 화면에서 누락',
  'expected_buys':1,'actual':frontend['openPosition'],'source':'../backtest-console/src/features/backtest/utils/chartDataTransform.ts:146'},
 {'id':'R08','priority':'P2','kind':'residual','title':'동일 비중이 종목 순서에 따라 다른 금액으로 배분',
  'expected':'동일한 종목별 배분 또는 합계 오류의 명시적 거부','actual':permuted,
  'source':'../backtest-console/src/features/backtest/model/backtestFormReducer.ts:23'},
 {'id':'R09','priority':'P2','kind':'residual','title':'실제 달력에 존재하는 DCA 납입 일정 거부',
  'expected_dates':['2023-01-30','2023-03-27'],'frontend_periods':frontend['monthly2Periods'],
  'actual_http':http['monthly_2_calendar']['status'],'source':'backtest_be_rust/src/model.rs:157'},
 {'id':'R10','priority':'P2','kind':'regression','title':'유한 입력의 연율화 오버플로가 panic/HTTP 500 발생',
  'expected':'성공 또는 명시적 422; panic 금지',
  'actual_http':[http[n]['status'] for n in ['finite_annual_overflow','finite_short_listing_overflow']],
  'source':'backtest_be_rust/src/strategy.rs:288'},
 {'id':'R11','priority':'P3','kind':'residual','title':'현금 이름 date가 비중 이력 날짜를 덮어씀',
  'expected_date':'2023-01-02','actual':engine['cash_date_key']['data']['weight_history'][0],
  'scope':'직접 API에서 소문자 현금 이름 date를 사용한 경우; UI는 대문자로 변환',
  'source':'backtest_be_rust/src/engine.rs:642'},
]
old=json.loads((ROOT/'comparison/adversarial/corrected-evidence-2026-11-11.json').read_text(encoding='utf8'))
changed=[p for p,h in old['source_sha256'].items() if hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()!=h]
assert not changed,changed
evidence={'date':'2026-11-11','basis':'Independent synthetic arithmetic and actual source/runtime probes. Python outputs are not an oracle.',
 'unchanged_prior_manifest_files':len(old['source_sha256']),'source_sha256':read('source-hashes.json'),
 'runtime_images':{'api':'sha256:08b07b170a82cb9de3ade7b703bd02df4055367917858a89d40bb9fecf375cf0',
                   'console':'sha256:263444bdab018b109b0dd786880d5e7fa444da2b93f0ae6217142bae7b2cecc2'},
 'baseline':{k:v for k,v in read('baseline/checks.json').items() if k!='checks_detail'},
 'ordinary_rust_tests':{'passed':24,'ignored_db_tests':2,'command':'cargo test --offline'},
 'fresh_engine_cases':len(engine),'before_control_cases':len(before),'http_cases':len(http),
 'http_statuses':{k:v['status'] for k,v in http.items()},
 'findings':findings,'regressions':5,'residuals':6,'severity_counts':{'P1':4,'P2':6,'P3':1},
 'limitations':['Synthetic holiday/price scenarios do not assert those values happened in live markets.',
 'Frontend checks execute actual reducers/validators/chart transformations; no fresh full-browser E2E in this round.',
 'Cache race uses unchanged cached/save methods in an isolated MySQL; the frequency is not a production incidence estimate.',
 'Undefined metric fallbacks and previously documented modeling assumptions are not counted again.',
 'Application code, user-facing containers and their DB volumes were not changed.']}
out=ROOT/'comparison/adversarial/readversarial-evidence-2026-11-11.json'
out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'findings':len(findings),'expected_rebalanced':expected_rebalanced,'expected_fx':expected_fx,'expected_profit_factor':expected_pf,'source_manifest_unchanged':len(old['source_sha256'])}))
