"""Verify and archive independently reproduced findings from the third audit."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
REPORT=ROOT/'.comparison/reports/third-audit-2026-11-11'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
outputs={c['name']:c['output']['data'] for c in read(REPORT/'engine-results.json')}
before={c['name']:c['output']['data'] for c in read(REPORT/'before/engine-results.json')}
front=read(REPORT/'frontend-results.json')
charts={c['name']:c for c in front['normalized']}
markers={c['name']:c for c in front['markers']}
http=read(REPORT/'http-results.json')
assert len(http)==16 and all(c['status']==200 for c in http)
for c in http:
    assert c['output']['data']['portfolio_statistics']==outputs[c['name']]['portfolio_statistics']
manifest=read(REPORT/'source-sha256.json')
assert len(manifest)==202
assert all(hashlib.sha256((ROOT.parent/p).read_bytes()).hexdigest()==h for p,h in manifest.items())
baseline=read(REPORT/'baseline/checks.json')
assert baseline['passed']==202 and baseline['failed']==0
omit={'timestamp','execution_time_seconds'}
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items() if k not in omit}
    if isinstance(v,list):return [clean(x) for x in v]
    return v
assert clean(read(REPORT/'previous/engine-results.json'))==clean(read(ROOT/'.comparison/reports/second-corrected-2026-11-11/engine-results.json'))
near=lambda a,b:math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9)

split_actual=[outputs[n]['portfolio_statistics']['Final_Value'] for n in ['split_unit_1','split_unit_0.5']]
assert split_actual==[14770,15035]
assert all(outputs['split_fractional_control_'+f]['portfolio_statistics']['Final_Value']==15000 for f in ['1','0.5'])
assert all(outputs[n]['portfolio_statistics']['Final_Value']==before[n]['portfolio_statistics']['Final_Value'] for n in ['split_unit_1','split_unit_0.5','initial_fee','weekend_cash_weights','late_initial_weights'])
initial=outputs['initial_fee'];expected_index=100/1.01
assert near(initial['portfolio_statistics']['Time_Weighted_Return'],expected_index-100)
assert all(r==0 for r in initial['daily_returns'].values()) and charts['initial_fee']['lastIndex']==100
assert charts['front_loaded_gain_40']['lastIndex']==120
assert charts['front_loaded_gain_800']['lastIndex']==charts['front_loaded_gain_monthly']['lastIndex']==100
assert markers['weekly_backdated_open']['entries'][0]['EntryTime']=='2023-01-11'
assert markers['weekly_backdated_open']['points'][0]=={'date':'2023-01-09','price':100,'buySignal':100}
assert markers['open_close_gap']['entries'][0]['EntryPrice']==97 and markers['open_close_gap']['points'][0]['buySignal']==110
assert outputs['weekend_cash_weights']['weight_history'][0]=={'date':'2023-01-01'}
assert outputs['late_initial_weights']['weight_history'][0]=={'date':'2023-01-02','TEST':.5}
csv_rows=list(csv.reader((REPORT/'rebalance_csv_fees.csv').read_text(encoding='utf8').splitlines()))
idx=next(i for i,r in enumerate(csv_rows) if r and r[0]=='리밸런싱 히스토리')+2
trade_rows=[]
while csv_rows[idx]:trade_rows.append(csv_rows[idx]);idx+=1
fees=outputs['rebalance_csv_fees']['rebalance_history']
actual_fees=sum(e['commission_cost'] for e in fees)
export_fees=sum(float(r[-1]) for r in trade_rows)
assert near(actual_fees,66.76780501779085) and near(export_fees,133.52)
weight_csv=(REPORT/'weekend_cash_weights.csv').read_text(encoding='utf8').split('포트폴리오 비중 변화')[1]
assert 'TEST' not in weight_csv

findings=[
 {'id':'S01','priority':1,'classification':'residual','title':'Adjusted price units are rounded as real integer shares',
  'cases':['split_unit_1','split_unit_0.5'],'expected_final_in_both_units':14770,'actual_final':split_actual,
  'fractional_control_final':[15000,15000],'scope':'Synthetic split-unit counterfactual, not a live Yahoo corporate-action replay.'},
 {'id':'S02','priority':2,'classification':'residual','title':'Initial commission is omitted from the daily performance/normalized chart anchor',
  'expected_index':expected_index,'actual_index':100,'api_twr':initial['portfolio_statistics']['Time_Weighted_Return']},
 {'id':'S03','priority':2,'classification':'residual','title':'Weekly/monthly comparison drops the first return bucket',
  'expected_index':120,'actual_index':{'daily':120,'weekly':100,'monthly':100}},
 {'id':'S04','priority':2,'classification':'residual logic exposed by new open-position display path',
  'title':'Trade markers replace the actual entry date/price with sampled date/close',
  'actual_entry':{'date':'2023-01-11','price':98},'rendered_point':{'date':'2023-01-09','price':100},
  'daily_gap_entry':97,'daily_gap_marker':110},
 {'id':'S05','priority':2,'classification':'residual','title':'Uninvested cash is missing from weights and first-row CSV column discovery loses assets',
  'account_value':10000,'expected_weight_sum':1,'actual_first_weight_sums':[0,.5],'weekend_csv_asset_columns':0},
 {'id':'S06','priority':2,'classification':'residual logic exposed by restored holiday rebalance path',
  'title':'CSV repeats total event commission on every trade row',
  'actual_fee_total':actual_fees,'csv_fee_total':export_fees,'first_event_fee':fees[0]['commission_cost'],
  'first_event_trade_fees':[t['commission'] for t in fees[0]['trades']], 'first_event_csv_rows':trade_rows[:2]},
]
result={'date':'2026-11-11','basis':'Independent ledgers, split-unit invariance, date causality and response/UI/CSV reconciliation. Python financial outputs are not an oracle.',
 'source_manifest_unchanged':202,'source_sha256':manifest,'ordinary_rust_tests':{'passed':32,'failed':0,'db_ignored_not_rerun':3},
 'frontend_tests':{'files':42,'passed':382,'failed':0},'baseline':{k:baseline[k] for k in ['cases','checks','passed','failed']},
 'previous_engine_cases_unchanged':16,'fresh_engine_cases':16,'pre_fix_control_cases':16,'runtime_http_cases':16,
 'runtime_http_statuses':{c['name']:c['status'] for c in http},'runtime_images':(REPORT/'runtime-images.txt').read_text(encoding='utf-8-sig'),
 'runtime_binary':(REPORT/'runtime-binary.txt').read_text(encoding='utf-8-sig').strip(),
 'findings':findings,'severity_counts':{'P1':1,'P2':5},'new_engine_regression_confirmed':0,
 'regression_qualification':'No new engine regression confirmed in these scenarios; not a proof of absence. S04/S06 reuse pre-existing faulty consumers through recently corrected producer paths.',
 'limits':['No application source or running comparison service was changed.','Frontend evidence executes current source callbacks and CSV function; no fresh full browser UI run.',
 'DB concurrency tests were excluded in this round; prior results were not re-counted.','Split scenario models equivalent adjusted units and integer lots, not a live provider corporate-action reconstruction.']}
(ROOT/'comparison/adversarial/third-audit-evidence-2026-11-11.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'findings':len(findings),'severity':result['severity_counts'],'baseline_checks':202,'previous_cases':16,'new_http_cases':16,'fees':{'actual':actual_fees,'exported':export_fees}},ensure_ascii=False))
