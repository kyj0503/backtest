"""Archive the R01-R11 fixes without changing historical audit evidence."""
import hashlib
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / '.comparison/reports/second-corrected-2026-11-11'
MEMORY = ROOT / '.comparison/reports/second-corrected-memory-2026-11-11'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

checks = read(REPORT / 'second-checks.json')
baseline = read(REPORT / 'baseline/checks.json')
assert checks['passed'] == 34 and checks['failed'] == 0
assert baseline['passed'] == 202 and baseline['failed'] == 0
ui = read(REPORT / 'live-ui/ui.json')
assert len(ui) == 4 and all(x['statuses'] == [200] * 5 and not x['pageErrors'] for x in ui)
runtime = read(REPORT / 'runtime.json')
assert len(runtime) == 6 and all(x['health'] == 'healthy' for x in runtime)
http = read(REPORT / 'http-results.json')
assert len(http) == 16

def p95(values):
    return sorted(values)[math.ceil(len(values) * .95) - 1]

servers = {}
case_rows = {}
for name in ['python', 'rust']:
    r = read(MEMORY / (name + '.json'))
    assert len(r['cases']) == 35 and 'end' in r
    replies = [v for c in r['cases'] for v in c['responses']]
    sequential = [v['ms'] for c in r['cases'] if c['concurrency'] == 1 for v in c['responses']]
    assert len(replies) == 346 and all(v['status'] == 200 for v in replies)
    servers[name] = {
        'requests': len(replies), 'success_200': len(replies),
        'sequential_median_ms': statistics.median(sequential), 'sequential_p95_ms': p95(sequential),
        'idle_mib': r['idle']['current'] / 2**20,
        'observed_peak_mib': max(c['observed_peak']['current'] for c in r['cases']) / 2**20,
        'kernel_peak_mib': r['end']['kernel_peak'] / 2**20,
        'rss_peak_mib': r['end']['hwm'] / 2**20,
        'sequential_peak_mib': max(c['observed_peak']['current'] for c in r['cases'] if c['concurrency'] == 1) / 2**20,
        'end_mib': r['end']['current'] / 2**20,
        'swap_bytes': max(c['observed_peak']['swap'] for c in r['cases']),
        'memory_events': r['memory_events'],
        'sampling_interval_median_ms': statistics.median(c['interval_median_ms'] for c in r['cases']),
    }
    case_rows[name] = {c['name']: {
        'concurrency': c['concurrency'], 'requests': len(c['responses']),
        'median_ms': statistics.median(v['ms'] for v in c['responses']),
        'p95_ms': p95([v['ms'] for v in c['responses']]),
        'observed_peak_mib': c['observed_peak']['current'] / 2**20,
    } for c in r['cases']}

prior = read(ROOT / 'comparison/adversarial/corrected-evidence-2026-11-11.json')
quote_hash = sha(ROOT / '.comparison/reports/corrected-2026-11-11/benchmark-inputs/prices.json')
assert quote_hash == prior['benchmark']['conditions']['quotes_sha256']
sources = {}
for base, folder, extensions in [
    (ROOT, ROOT / 'backtest_be_rust', {'.rs', '.toml', '.lock', '.json'}),
    (ROOT.parent / 'backtest-console', ROOT.parent / 'backtest-console/src', {'.ts', '.tsx'}),
]:
    for p in folder.rglob('*'):
        if p.is_file() and p.suffix in extensions and 'target' not in p.parts:
            sources[base.name + '/' + p.relative_to(base).as_posix()] = sha(p)
for p in (ROOT / 'backtest_be_rust/src').glob('*.rs'):
    assert p.read_bytes() == (ROOT / '.comparison/second-correctness-crate/src' / p.name).read_bytes()
deployed_frontend = read(REPORT / 'frontend-runtime-source-hashes.json')
assert deployed_frontend
assert all(sources['backtest-console/' + path] == digest for path, digest in deployed_frontend.items())
for name in ['parity.json', 'real-market-python.json']:
    key = 'backtest/backtest_be_rust/tests/fixtures/' + name
    assert sources[key] == prior['source_sha256'][key], 'Historical Python outputs were changed'

benchmark = {
    'conditions': {'cases': 32, 'repeats': 10, 'concurrency': [2, 8, 16], 'cpus': 2,
                   'memory_limit_gib': 2, 'processes': 1, 'quotes_sha256': quote_hash,
                   'basis': 'Identical captured quotes and requests; full HTTP calculation; excludes external quote/DB I/O; observer in separate cgroup; 1 ms requested sampling.'},
    'servers': servers, 'per_case': case_rows,
    'prior_rust': prior['benchmark']['servers']['rust'],
}
manifest = {
    'date': '2026-11-11', 'fixed_findings': [f'R{i:02}' for i in range(1, 12)],
    'basis': 'Independent cash/share ledgers, calendar dates, net realized PnL, UI budget conservation. Python outputs are not an oracle.',
    'regressions': {'rust_ordinary': 32, 'disposable_mysql': 3, 'frontend': 382,
                    'new_rust_ordinary': 8, 'new_mysql': 1, 'new_frontend': 11},
    'independent_baseline': baseline, 'independent_second': checks,
    'cache_race': read(REPORT / 'cache-race.json'), 'frontend': read(REPORT / 'frontend-results.json'),
    'http': [{'name': x['name'], 'status': x['status']} for x in http],
    'browser': ui, 'runtime': runtime, 'deployed_frontend_source_files_matched': len(deployed_frontend),
    'binary_sha256': '8d9d6c0886c8c5c92727f11570d197a2b993b2c37d9ba342e0ec71d0f7d9c5ef',
    'binary_comparison': 'Same sha256 observed via docker exec in live Rust, fixture HTTP and benchmark containers.',
    'benchmark': benchmark, 'source_sha256': sources,
    'changed_since_previous_fix': [p for p, h in prior['source_sha256'].items() if sources.get(p) != h],
    'limits': 'Controlled local benchmark, not production latency or long-duration leak proof. Scope and contract changes are in the accompanying review.',
}
(MEMORY / 'summary.json').write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding='utf8')
(ROOT / 'comparison/adversarial/second-corrected-evidence-2026-11-11.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
rows = ['| 시나리오 | 동시 요청 | Python 중앙값 ms | Rust 중앙값 ms | Python 관측 최대 MiB | Rust 관측 최대 MiB |',
        '|---|---:|---:|---:|---:|---:|']
for name, a in case_rows['python'].items():
    b = case_rows['rust'][name]
    rows.append(f"| {name} | {a['concurrency']} | {a['median_ms']:.2f} | {b['median_ms']:.2f} | {a['observed_peak_mib']:.2f} | {b['observed_peak_mib']:.2f} |")
(REPORT / 'benchmark-table.md').write_text('\n'.join(rows) + '\n', encoding='utf8')
print(json.dumps({'checks': 236, 'source_files': len(sources), 'servers': servers}, ensure_ascii=False, indent=2))
