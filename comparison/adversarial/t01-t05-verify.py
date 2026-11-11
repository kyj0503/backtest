"""Re-execute the preserved fourth-audit inputs against corrected code/image."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.comparison/reports/t01-t05-2026-11-11'
OLD=ROOT/'.comparison/reports/fourth-audit-2026-11-11'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
def prepare():
    for sub in ['', 'baseline', 's01_s06']:
        dest=OUT/sub;dest.mkdir(parents=True,exist_ok=True)
        shutil.copy(OLD/sub/'cases.json',dest/'cases.json')
    shutil.copy(OLD/'http-cases.json',OUT/'http-cases.json')
    fixtures=read(OLD/'http-fixtures.json')
    bad=copy.deepcopy(next(iter(fixtures.values())));bad['symbol']='BADOPEN';bad['bars'][20]['open']=1.
    fixtures['BADOPEN']=bad
    # Shared server also replays the prior S01-S06 HTTP and browser scenarios.
    fixtures.update(read(ROOT/'.comparison/reports/s01-s06-2026-11-11/http-fixtures.json'))
    save(OUT/'http-fixtures.json',fixtures)
    shutil.copy(ROOT/'.comparison/reports/s01-s06-2026-11-11/http-cases.json',OUT/'s01_s06/http-cases.json')
    crate=ROOT/'.comparison/t01-t05-crate';crate.mkdir(exist_ok=True)
    for name in ['src','tests']:shutil.copytree(ROOT/'backtest_be_rust'/name,crate/name,dirs_exist_ok=True,copy_function=shutil.copy)
    for name in ['Cargo.toml','Cargo.lock','openapi.json']:shutil.copy(ROOT/'backtest_be_rust'/name,crate/name)
    (crate/'examples').mkdir(exist_ok=True)
    shutil.copy(Path(__file__).with_name('runner.rs'),crate/'examples/verify.rs')
    shutil.copy(Path(__file__).with_name('fourth_provider.rs'),crate/'examples/provider.rs')

def evaluate():
    spec=importlib.util.spec_from_file_location('fourth',Path(__file__).with_name('fourth_audit.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.OUT=OUT;module.evaluate()
    checks=read(OUT/'checks.json');assert checks['confirmed_failures']==0
    # U01/U02 are explicit policy questions, not T01-T05 fixes.
    assert checks['policy_discrepancies']==3
    provider=read(OUT/'provider-results.json')
    for p in provider:
        if p['name'] in ['adjusted_control','execution_control']:
            expected=10000 if p['name']=='adjusted_control' else 12375
            assert p['output']['engine']['data']['portfolio_statistics']['Final_Value']==expected
        else:assert p['output']['error_code']==503,p['name']
    print('T01/T02 provider controls and five explicit rejections passed')

def http():
    engine={c['name']:c['output'] for c in read(OUT/'engine-results.json')}
    results=[]
    cases=read(OUT/'http-cases.json')
    bad=copy.deepcopy(cases[0]);bad['name']='invalid_ohlc_http';bad['request']['portfolio']=[{'symbol':'BADOPEN','amount':10000}];cases.append(bad)
    for c in cases:
        for attempt in range(2 if c['name']=='late_listing_cash' else 1):
            req=urllib.request.Request('http://127.0.0.1:8002/api/v1/backtest',json.dumps(c['request']).encode(),{'Content-Type':'application/json'})
            try:
                with urllib.request.urlopen(req,timeout=60) as response:status=response.status;value=json.load(response)
            except urllib.error.HTTPError as response:status=response.code;value=json.load(response)
            row=dict(name=c['name'],attempt=attempt+1,status=status,output=value);results.append(row)
            save(OUT/'http-results.json',results)
            if c['name']=='invalid_ohlc_http':assert status==503,value
            else:
                assert status==200,value
                actual=value['data']['portfolio_statistics'];expected=engine[c['name']]['data']['portfolio_statistics']
                for k in ['Final_Value','Time_Weighted_Return','Max_Drawdown']:assert abs(actual[k]-expected[k])<1e-7,(c['name'],k,actual[k],expected[k])
    print(json.dumps(dict(calls=len(results),success=sum(r['status']==200 for r in results),rejected_invalid_ohlc=sum(r['status']==503 for r in results))))

if __name__=='__main__':{'prepare':prepare,'evaluate':evaluate,'http':http}[sys.argv[1]]()
