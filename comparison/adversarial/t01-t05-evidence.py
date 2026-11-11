"""Hash verified sources and summarize independent checks and controlled benchmarks."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.comparison/reports/t01-t05-2026-11-11'
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
def sources():
    paths=list((ROOT/'backtest_be_rust/src').rglob('*.rs'))+list((ROOT/'backtest_be_rust/tests').rglob('*'))
    paths+=list((ROOT.parent/'backtest-console/src').rglob('*.ts'))+list((ROOT.parent/'backtest-console/src').rglob('*.tsx'))
    paths += [ROOT/'backtest_be_rust'/n for n in ['Cargo.toml','Cargo.lock','Dockerfile','openapi.json']]
    paths += [ROOT.parent/'backtest-console'/n for n in ['package.json','package-lock.json','Dockerfile']]
    return {p.relative_to(ROOT.parent).as_posix():sha(p) for p in paths if p.is_file()}
def benchmark(path):
    d=read(path);responses=[r for c in d['cases'] for r in c['responses']]
    sequential=sorted(r['ms'] for c in d['cases'] if c['concurrency']==1 for r in c['responses'])
    assert len(responses)==346 and all(r['status']==200 for r in responses)
    return dict(source=str(path.relative_to(ROOT)),sha256=sha(path),requests=len(responses),
        median_ms=statistics.median(sequential),p95_ms=sequential[math.ceil(len(sequential)*.95)-1],
        idle_mib=d['idle']['current']/2**20,kernel_peak_mib=d['end']['kernel_peak']/2**20,
        rss_high_water_mib=d['end']['hwm']/2**20,
        swap_bytes=d['end']['swap'],memory_events=d['memory_events'],
        scenarios=[dict(name=c['name'],concurrency=c['concurrency'],median_ms=statistics.median(r['ms'] for r in c['responses']),observed_peak_mib=c['observed_peak']['current']/2**20) for c in d['cases']])
def seal():
    snap=read(OUT/'verified-source.json');assert sources()==snap,'Verified source changed after checks'
    for p in (ROOT/'backtest_be_rust/src').rglob('*.rs'):
        assert sha(p)==sha(ROOT/'.comparison/t01-t05-crate/src'/p.relative_to(ROOT/'backtest_be_rust/src'))
    benchmarks={label:benchmark(ROOT/'.comparison/reports'/folder/file) for label,folder,file in [
        ('before_rust','t01-t05-before-memory-2026-11-11','rust.json'),
        ('rust','t01-t05-memory-2026-11-11','rust.json'),
        ('python','t01-t05-memory-2026-11-11','python.json')]}
    names=['backtest-compare-python-api-1','backtest-compare-rust-api-1','backtest-compare-python-console-1','backtest-compare-rust-console-1']
    inspect=json.loads(subprocess.check_output(['docker','inspect',*names],text=True,encoding='utf8'))
    runtime=[dict(name=c['Name'].lstrip('/'),image=c['Image'],health=c['State']['Health']['Status'],restarts=c['RestartCount']) for c in inspect]
    assert all(c['health']=='healthy' for c in runtime)
    binary=subprocess.check_output(['docker','exec','backtest-compare-rust-api-1','sha256sum','/usr/local/bin/backtest-server'],text=True).split()[0]
    provider=read(OUT/'provider-results.json')
    http=read(OUT/'http-results.json')
    front=read(OUT/'fourth-frontend-results.json')
    assert len(front)==1 and front[0]['exportedQuantity']>0 and abs(front[0]['reconstructedNotional']-50)<1e-8
    fourth=read(OUT/'checks.json');assert fourth['confirmed_failures']==0 and fourth['policy_discrepancies']==3
    baseline=read(OUT/'baseline/checks.json');assert baseline['failed']==0
    prior=read(OUT/'s01_s06/http-checks.json');assert prior['failed']==0
    new_browser=read(OUT/'t01-t05-browser.json');old_browser=read(OUT/'s01_s06/browser.json')
    assert len(new_browser)==4 and len(old_browser)==5
    for b in new_browser+old_browser:assert b['statuses']==[200]*5 and not b['pageErrors']
    data=dict(date='2026-11-11',scope='T01-T05 fixed; independent accounting, not Python parity',
        tests=dict(rust_regular_passed=55,mysql_passed=5,frontend_passed=397,frontend_files=44,
            added_rust_regular=7,added_mysql=2,added_frontend_cases=5,
            baseline={k:baseline[k] for k in ['cases','checks','passed','failed']},
            new_engine={k:v for k,v in fourth.items() if k!='details'},
            s01_s06_http={k:prior[k] for k in ['http_cases','checks','passed','failed']},
            t01_t05_http_calls=len(http),t01_t05_http_success=sum(r['status']==200 for r in http),
            t02_http_rejected=sum(r['status']==503 for r in http),browser_runs=len(new_browser)+len(old_browser),browser_http_200=45),
        provider=[dict(name=p['name'],error_code=p['output'].get('error_code'),statistics=p['output'].get('engine',{}).get('data',{}).get('portfolio_statistics')) for p in provider],
        csv=front,browser=new_browser+old_browser,policy_questions_retained=['U01 equality crossing','U02 buy-and-hold benchmark start'],
        benchmarks=benchmarks,runtime=runtime,rust_binary_sha256=binary,source_sha256=snap,
        artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()})
    save(Path(__file__).with_name('t01-t05-evidence-2026-11-11.json'),data)
    print(json.dumps({k:{x:v for x,v in b.items() if x!='scenarios'} for k,b in benchmarks.items()},ensure_ascii=False,indent=2))
    print(json.dumps(dict(source_files=len(snap),runtime=runtime,rust_binary_sha256=binary),ensure_ascii=False))

if __name__=='__main__':
    if sys.argv[1]=='snapshot':save(OUT/'verified-source.json',sources())
    else:seal()
