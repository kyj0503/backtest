"""Local runtime HTTP verification with synthetic price/news fixtures.

Run directly, after seeding an isolated local stack as described in
docs/architecture/api-boundaries.md. Never connects to a production hostname.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request


def verify(base, token=None):
    def call(path, payload=None):
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {'Content-Type': 'application/json'}
        if payload is not None and token:
            headers['X-Turnstile-Token'] = token
        req = urllib.request.Request(base + path, data=body, headers=headers)
        try:
            response = urllib.request.urlopen(req, timeout=35)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            data = json.loads(response.read())
            return response.status, data

    flags = {f'include_{section}': False for section in (
        'news', 'benchmarks', 'exchange_rates', 'stock_data', 'volatility_events')}
    request = {'portfolio': [{'symbol': 'CASH', 'amount': 1500, 'asset_type': 'cash'}],
               'start_date': '2023-01-01', 'end_date': '2023-12-31',
               'strategy': 'buy_hold_strategy', 'rebalance_frequency': 'none', **flags}
    code, cash = call('/api/v1/backtest', request)
    assert code == 200 and cash['data']['portfolio_statistics']['Final_Value'] == 1500
    request['portfolio'] = [{'symbol': 'AAPL', 'amount': 1000, 'asset_type': 'stock'}]
    code, core = call('/api/v1/backtest', request)
    assert code == 200 and core['data']['equity_curve']
    assert math.isfinite(core['data']['portfolio_statistics']['Final_Value'])
    period = urllib.parse.urlencode({'start_date': request['start_date'], 'end_date': request['end_date']})
    paths = [
        '/api/v1/prices?' + period + '&symbols=AAPL',
        '/api/v1/exchange-rates?' + period,
        '/api/v1/benchmarks?' + period,
        '/api/v1/news?symbols=AAPL&limit=1',
    ]
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(call, paths))
    assert [code for code, _ in responses] == [200] * 4
    prices, exchange, benchmarks, news = [data['data'] for _, data in responses]
    assert len(prices['stock_data']['AAPL']) > 200
    assert len(exchange['exchange_rates']) > 200
    assert benchmarks['sp500_total_return_pct'] is not None
    assert len(news['latest_news']['AAPL']) == 1
    assert 'LOCAL FIXTURE NEWS' in news['latest_news']['AAPL'][0]['title']
    expected = [
        {'ticker_info', 'stock_data', 'volatility_events', 'supplemental_status'},
        {'exchange_rates', 'exchange_stats', 'supplemental_status'},
        {'sp500_benchmark', 'nasdaq_benchmark', 'sp500_total_return_pct', 'supplemental_status'},
        {'latest_news', 'supplemental_status'},
    ]
    assert all(set(data) == fields for data, fields in zip((prices, exchange, benchmarks, news), expected))
    for path in ('/api/v1/news?symbols=AAPL&start_date=2023-01-01',
                 '/api/v1/prices?' + period + '&symbols=../bad'):
        assert call(path)[0] == 422
    assert call('/api/v1/market-data?' + period)[0] == 404
    # The existing POST still offers its legacy all-in-one response.
    legacy = {key: value for key, value in request.items() if not key.startswith('include_')}
    code, full = call('/api/v1/backtest', legacy)
    assert code == 200
    for key in ('equity_curve', 'daily_returns', 'individual_returns', 'portfolio_composition', 'strategy_details'):
        assert full['data'][key] == core['data'][key], key
    statistics = {key: value for key, value in full['data']['portfolio_statistics'].items()
                  if key not in ('sp500_total_return_pct', 'alpha_vs_sp500_pct')}
    assert statistics == core['data']['portfolio_statistics']
    return {'four_parallel_reads': True, 'resource_fields_isolated': True,
            'news_without_period': True, 'invalid_queries_rejected': True,
            'cash_1500_preserved': True, 'legacy_calculation_values_preserved': True,
            'old_aggregate_get_removed': True, 'price_points': len(prices['stock_data']['AAPL'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:18080')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    url = urllib.parse.urlsplit(args.base_url)
    if url.scheme != 'http' or url.hostname not in ('localhost', '127.0.0.1', '::1'):
        parser.error('Only a local HTTP test stack is allowed')
    # Only documented dummy tokens, against the localhost restriction above.
    report = verify(args.base_url.rstrip('/'), os.getenv('TURNSTILE_TEST_TOKEN'))
    if args.report:
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
