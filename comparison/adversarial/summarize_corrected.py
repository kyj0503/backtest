"""Archive the corrected implementation's evidence without altering the audit."""
import hashlib
import json
import subprocess
from pathlib import Path

repo=Path(__file__).resolve().parents[2]
frontend=repo.parent/'backtest-console'
root=repo/'.comparison/reports/corrected-2026-11-11'
read=lambda name: json.loads((root/name).read_text(encoding='utf-8'))
checks=read('checks.json')
assert checks['cases']==133 and checks['failed']==0 and checks['passed']==202
assert read('database-migrate-local.json')['schema_parity']
ui=read('browser-python/ui.json')+read('browser-rust/ui.json')
assert len(ui)==7 and all(not x['pageErrors'] and x['statuses']==[200]*5 for x in ui)
assert next(x for x in ui if x['scenario']=='weight_dca')['request']['portfolio'][0]['total_amount']==10000
benchmark=read('benchmark/summary.json')
assert all(r['success_200']==346 for r in benchmark['servers'].values())
assert len(read('benchmark-verification.json'))==64
sources={}
for base,folder,extensions in [(repo,repo/'backtest_be_rust', {'.rs','.toml','.lock','.json'}),
                               (frontend,frontend/'src',{'.ts','.tsx'})]:
    for p in folder.rglob('*'):
        if p.is_file() and p.suffix in extensions and 'target' not in p.parts:
            sources[base.name+'/'+p.relative_to(base).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest()
for p in (repo/'backtest_be_rust/src').glob('*.rs'):
    assert p.read_bytes()==(repo/'.comparison/correctness-crate/src'/p.name).read_bytes()
for name in ['parity.json','real_parity.json']:
    a=repo/'backtest_be_rust/tests/fixtures'/name
    b=repo/'.comparison/adversarial-crate/tests/fixtures'/name
    if a.exists() and b.exists():assert a.read_bytes()==b.read_bytes(),'Historical Python expectations changed'
names=['backtest-compare-'+x+'-1' for x in ['python-api','rust-api','python-console','rust-console']]
containers=json.loads(subprocess.check_output(['docker','inspect',*names],encoding='utf-8'))
runtime=[{'name':c['Name'],'image_id':c['Image'],'status':c['State']['Status'],
          'health':c['State'].get('Health',{}).get('Status'),
          'cpu_limit':c['HostConfig']['NanoCpus']/1e9,'memory_limit':c['HostConfig']['Memory']} for c in containers]
assert all(c['status']=='running' and c['health']=='healthy' for c in runtime)
manifest={'date':'2026-11-11','basis':'Independent arithmetic, causal fills, self-financing ledger, contribution conservation; Python financial outputs are not an oracle',
          'branches':{p.name:subprocess.check_output(['git','-C',str(p),'branch','--show-current'],encoding='utf-8').strip() for p in [repo,frontend]},
          'fixed_findings':[f'F{i:02d}' for i in range(1,17)],'engine':checks,
          'rust_tests':{'ordinary':24,'disposable_mysql':2,'historical_inputs':70},
          'frontend_tests':371,'frontend':read('frontend-results.json'),
          'http':[{'name':r['name'],'http_status':r['status'],'statistics':r['output'].get('data',{}).get('portfolio_statistics')} for r in read('http-results.json')],
          'database':read('database-migrate-local.json'),'browser':ui,
          'benchmark':benchmark,'runtime':runtime,'source_sha256':sources,
          'remaining_limits':'See docs/reviews/rust-correctness-fixes-2026-11-11.md; no claim of all-market correctness or long-term leak freedom.'}
destination=repo/'comparison/adversarial/corrected-evidence-2026-11-11.json'
destination.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Corrected evidence archived: {checks["passed"]} checks; {len(ui)} UI scenarios; 692 benchmark requests; {len(sources)} source hashes')
