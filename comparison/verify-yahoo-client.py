"""Check the final Rust API against separately decoded Yahoo historical data.

Use an isolated API without a database/fixture file so every first read exercises
the production YahooConnector. Historical raw responses and checks are retained.
"""
import argparse
import datetime as dt
import json
import math
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, quote
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def get(url):
    start = time.perf_counter()
    try:
        with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Backtest/1.7.10)"}), timeout=60) as r:
            return r.status, json.load(r), (time.perf_counter()-start)*1000
    except HTTPError as e:
        return e.code, {"error": e.read().decode(errors="replace")}, (time.perf_counter()-start)*1000


def memory_snapshot():
    # Only enabled when the observer shares the target's PID namespace while
    # retaining its own cgroup, as in benchmark-memory.py.
    group = next(v for v in Path('/proc/1/cgroup').read_text().splitlines() if v.startswith('0::'))
    assert group not in Path('/proc/self/cgroup').read_text().splitlines()
    root = Path('/sys/fs/cgroup')/group.split(':',2)[2].lstrip('/')
    return {key:int((root/('memory.'+key)).read_text()) for key in ['current','peak','swap.current']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observe-memory", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cases = [
        ("AAPL", "2020-08-24", "2020-09-04"),
        ("005930.KS", "2023-03-20", "2023-04-04"),
        ("7203.T", "2023-03-20", "2023-04-04"),
        ("KRW=X", "2023-03-20", "2023-04-04"),
        ("SAP.DE", "2023-10-23", "2023-11-03"),
        ("BTC-USD", "2023-03-20", "2023-04-04"),
        ("QQQ", "2015-01-02", "2023-12-29"),
    ]
    report = {"basis": "Independent Python standard-library date/price arithmetic against captured Yahoo responses, not the original Python backtest", "cases": []}
    if args.observe_memory:
        report['idle_memory'] = memory_snapshot()
    for symbol, first, last in cases:
        row = {"symbol": symbol, "start": first, "end": last}
        path = (
            "/api/v1/exchange-rates?" + urlencode({"start_date":first,"end_date":last})
            if symbol == "KRW=X" else
            "/api/v1/prices?" + urlencode({"symbols": symbol, "start_date": first, "end_date": last})
        )
        status, value, cold_ms = get(args.base + path)
        row.update(status=status, cold_ms=cold_ms)
        filename = symbol.replace("=", "_")
        (args.output / (filename + "-api.json")).write_text(json.dumps(value, ensure_ascii=False, indent=2))
        start = dt.datetime.fromisoformat(first).replace(tzinfo=dt.timezone.utc)-dt.timedelta(days=1)
        end = dt.datetime.fromisoformat(last).replace(tzinfo=dt.timezone.utc)+dt.timedelta(days=2)
        query = urlencode({"symbol":symbol,"period1": int(start.timestamp()), "period2": int(end.timestamp()), "interval": "1d", "events": "div|split|capitalGains"})
        raw_status, raw, raw_ms = get("https://query1.finance.yahoo.com/v8/finance/chart/"+quote(symbol,safe="")+"?"+query)
        row.update(reference_status=raw_status, reference_ms=raw_ms)
        (args.output / (filename + "-raw.json")).write_text(json.dumps(raw, ensure_ascii=False, indent=2))
        try:
            assert status == raw_status == 200, (status, raw_status)
            data = raw["chart"]["result"][0]
            q = data["indicators"]["quote"][0]
            adj = data["indicators"].get("adjclose", [{}])[0].get("adjclose", [None]*len(data["timestamp"]))
            tz = ZoneInfo(data["meta"]["exchangeTimezoneName"])
            expected = {}
            for i, timestamp in enumerate(data["timestamp"]):
                day = dt.datetime.fromtimestamp(timestamp, tz).date().isoformat()
                prices = [q[key][i] for key in ("open", "high", "low", "close")]
                if not first <= day <= last or not all(v is not None and math.isfinite(v) and v > 0 for v in prices):
                    continue
                expected[day] = adj[i] if adj[i] is not None else prices[3]
            body = value.get("data", value)
            actual = ([{"date":v["date"],"price":v["rate"]} for v in body["exchange_rates"]]
                      if symbol == "KRW=X" else body["stock_data"][symbol])
            assert expected, "The provider reference must contain prices"
            assert [v["date"] for v in actual] == sorted(expected), "Trading dates differ"
            max_error = max(abs(v["price"]-expected[v["date"]]) for v in actual)
            # Independent Yahoo HTTP responses can differ by a few float32 ULPs
            # in historical adjusted prices. This is a live smoke tolerance,
            # not the tolerance used for deterministic captured-response tests.
            assert all(math.isclose(v["price"], expected[v["date"]], rel_tol=1e-6, abs_tol=1e-10) for v in actual), "Adjusted prices differ beyond live provider tolerance"
            warm_status, warm, warm_ms = get(args.base + path)
            assert warm_status == 200 and warm == value, "Memory cache changes the response"
            row.update(passed=True, bars=len(actual), timezone=str(tz), currency=data["meta"].get("currency"), max_price_error=max_error,
                       max_relative_error=max(abs(v["price"]-expected[v["date"]])/expected[v["date"]] for v in actual),
                       live_relative_tolerance=1e-6,warm_ms=warm_ms)
        except (AssertionError, KeyError, TypeError, ValueError) as e:
            row.update(passed=False, error=str(e))
        report["cases"].append(row)
        print(json.dumps(row), flush=True)
        time.sleep(0.3)
    report["passed"] = sum(r["passed"] for r in report["cases"])
    report["failed"] = len(cases)-report["passed"]
    if args.observe_memory:
        report['end_memory'] = memory_snapshot()
    (args.output / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return bool(report["failed"])


if __name__ == "__main__":
    raise SystemExit(main())
