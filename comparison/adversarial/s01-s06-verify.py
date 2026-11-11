"""Recheck preserved S01–S06 synthetic inputs through the final runtime HTTP API.

Run with a DEBUG fixture server loaded with http-fixtures.json in the report
directory. Expectations below are independent accounting, never Python parity.
"""
import argparse
import json
import math
from pathlib import Path
import urllib.request


def verify(directory: Path, server: str):
    cases = json.loads((directory / 'http-cases.json').read_text(encoding='utf-8-sig'))
    outputs = []
    for case in cases:
        req = urllib.request.Request(server + '/api/v1/backtest',
            data=json.dumps(case['request']).encode(), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=45) as response:
            assert response.status == 200
            output = json.load(response)
        outputs.append({'name': case['name'], 'status': 200, 'output': output})
    (directory / 'http-results.json').write_text(json.dumps(outputs, ensure_ascii=False), encoding='utf8')
    data = {o['name']: o['output']['data'] for o in outputs}
    checks = []

    def near(name, actual, expected):
        passed = math.isclose(actual, expected, abs_tol=1e-7, rel_tol=1e-10)
        checks.append({'name': name, 'actual': actual, 'expected': expected, 'passed': passed})

    for name, d in data.items():
        wealth = math.prod(1 + r / 100 for r in d['daily_returns'].values())
        near(name + '/public_TWR', (wealth - 1) * 100, d['portfolio_statistics']['Time_Weighted_Return'])
        near(name + '/ending_equity', list(d['equity_curve'].values())[-1], d['portfolio_statistics']['Final_Value'])
        for row in d['weight_history']:
            near(name + '/weights/' + row['date'], sum(v for k, v in row.items() if k != 'date'), 1)
        for event in d['rebalance_history']:
            near(name + '/fee/' + event['date'], event['commission_cost'], sum(t['commission'] for t in event['trades']))
            for trade in event['trades']:
                near(name + '/trade_fee', trade['commission'], trade.get('shares', 0) * trade['price'] * .01)
    for factor in ['1', '0.5']:
        near('S01/unit/' + factor, data['split_unit_' + factor]['portfolio_statistics']['Final_Value'],
             10000 + (9500 / 980) * (1500 - 970))
        near('S01/control/' + factor, data['split_fractional_control_' + factor]['portfolio_statistics']['Final_Value'], 15000)
    near('S02/first_fee', data['initial_fee']['daily_returns']['2023-01-02'], (1 / 1.01 - 1) * 100)
    near('S02/final', data['initial_fee']['portfolio_statistics']['Final_Value'], 10000 / 1.01)
    for name in ['front_loaded_gain_40', 'front_loaded_gain_400', 'front_loaded_gain_800', 'front_loaded_gain_monthly']:
        near('S03/' + name, data[name]['portfolio_statistics']['Final_Value'], 12000)
    gap = next(iter(data['open_close_gap']['strategy_details'].values()))['trade_log'][0]
    near('S04/open_execution', gap['EntryPriceNative'], 97)
    assert gap['EntryTime'][:10] == '2023-01-05'
    summary = {'http_cases': len(outputs), 'checks': len(checks), 'passed': sum(c['passed'] for c in checks),
               'failed': sum(not c['passed'] for c in checks), 'details': checks}
    (directory / 'http-checks.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({k: v for k, v in summary.items() if k != 'details'}))
    assert summary['failed'] == 0, [c for c in checks if not c['passed']]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('directory', type=Path)
    parser.add_argument('--server', default='http://127.0.0.1:8002')
    args = parser.parse_args()
    verify(args.directory, args.server)
