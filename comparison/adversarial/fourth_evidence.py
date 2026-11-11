"""Seal review evidence and verify the audited application sources were unchanged."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.comparison/reports/fourth-audit-2026-11-11'
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
before=read(OUT/'source-before.json')
for name,digest in before.items():
    assert sha(ROOT.parent/name)==digest, 'Application source changed: '+name
for path in (ROOT/'backtest_be_rust/src').rglob('*.rs'):
    assert sha(path)==sha(ROOT/'.comparison/fourth-audit-crate/src'/path.relative_to(ROOT/'backtest_be_rust/src'))

# Compare with the saved pre-S01/S06 snapshot, whose hashes were recorded earlier.
prior=read(ROOT/'comparison/yahoo-client-evidence-2026-11-11.json')['source_sha256']
old=ROOT/'.comparison/yahoo-audit-crate'
for rel in ['src/data.rs','src/strategy.rs']:
    assert sha(old/rel)==prior['backtest_be_rust/'+rel]
old_strategy=(old/'src/strategy.rs').read_text()
strategy=(ROOT/'backtest_be_rust/src/strategy.rs').read_text()
loops='for i in warmup + 1..bars.len() {'
assert loops in old_strategy and loops in strategy
assert sha(old/'src/data.rs')==sha(ROOT/'backtest_be_rust/src/data.rs')
frontend=ROOT.parent/'backtest-console'
previous_csv=subprocess.check_output(['git','-C',str(frontend),'show','HEAD:src/features/backtest/services/reportGenerator.ts'],text=True,encoding='utf8')
assert 'trade.shares.toFixed(4)' in previous_csv

def stable(value):
    if isinstance(value,dict):return {k:stable(v) for k,v in value.items() if k not in ['timestamp','execution_time','execution_time_ms','execution_time_seconds']}
    if isinstance(value,list):return [stable(v) for v in value]
    return value
old_outputs=read(ROOT/'.comparison/reports/s01-s06-2026-11-11/engine-results.json')
new_outputs=read(OUT/'s01_s06/engine-results.json')
same=stable(old_outputs)==stable(new_outputs)
assert same,'Existing S01/S06 engine output drift'
new_checks=read(OUT/'checks.json')
baseline=read(OUT/'baseline/checks.json')
s01=read(OUT/'s01_s06/http-checks.json')
http=read(OUT/'http-results.json')
provider=read(OUT/'provider-results.json')
compact_provider=[]
for p in provider:
    d=p['output']['engine']['data']
    compact_provider.append(dict(name=p['name'],library_quotes_ok=p['library_quotes_ok'],
      bars=len(p['output']['history']['bars']),statistics=d['portfolio_statistics'],warnings=d.get('warnings'),
      strategy_details=d.get('strategy_details')))
names=['backtest-compare-python-api-1','backtest-compare-rust-api-1','backtest-compare-python-console-1','backtest-compare-rust-console-1']
containers=json.loads(subprocess.check_output(['docker','inspect',*names],text=True,encoding='utf8'))
runtime=[dict(name=c['Name'].lstrip('/'),image=c['Image'],health=c['State']['Health']['Status'],restarts=c['RestartCount']) for c in containers]
evidence=dict(date='2026-11-11',basis='Independent financial arithmetic and causal execution; Python service outputs not used',
 confirmed_findings=['T01 mixed adjusted and unadjusted prices','T02 impossible OHLC execution','T03 first valid Bollinger signal skipped','T04 listing date cache changes acceptance','T05 fractional CSV quantity rounded to zero'],
 policy_questions=['U01 equality crossover convention','U02 buy-and-hold benchmark start date'],
 tests=dict(rust_regular_passed=48,mysql_passed=3,frontend_passed=392,frontend_files=43,
   baseline={k:baseline[k] for k in ['cases','checks','passed','failed']},
   s01_s06_http={k:s01[k] for k in ['http_cases','checks','passed','failed']},
   s01_s06_engine_unchanged=same,s01_s06_chart_cases=16,s01_s06_marker_cases=15,
   new_engine={k:v for k,v in new_checks.items() if k!='details'},
   new_http_calls=len(http),new_http_200=sum(r['status']==200 for r in http),new_http_422=sum(r['status']==422 for r in http),
   provider_cases=len(provider),browser_rerun=False),
 new_engine_discrepancies=[c for c in new_checks['details'] if not c['passed']],provider=compact_provider,
 http=[dict(name=r['name'],attempt=r['attempt'],status=r['status'],engine_final=r['engine_final'],http_final=r['http_final'],error=r['output'].get('error')) for r in http],
 fractional_csv=read(OUT/'fourth-frontend-results.json'),
 provenance=dict(pre_s01_data_sha256=sha(old/'src/data.rs'),pre_s01_strategy_sha256=sha(old/'src/strategy.rs'),
   first_valid_bar_skip_present_before_s01=True,csv_rounding_present_in_frontend_head=subprocess.check_output(['git','-C',str(frontend),'rev-parse','HEAD'],text=True).strip(),
   regression_conclusion='No newly introduced S01-S06 regression confirmed in tested cases; confirmed findings pre-existed the patch'),
 runtime=runtime,rust_binary_sha256='dafebdeaf662c937b5fa1a851fda2fe0b5bd6b6350f36bcc7fcdbf2cd4f5b927',
 application_sources_unchanged=len(before),source_sha256=before,
 artifact_sha256={p.relative_to(OUT).as_posix():sha(p) for p in OUT.rglob('*') if p.is_file()})
dest=Path(__file__).with_name('fourth-evidence-2026-11-11.json')
dest.write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(dict(source_files_unchanged=len(before),s01_s06_outputs_unchanged=same,tests=evidence['tests'],runtime=runtime),ensure_ascii=False))
