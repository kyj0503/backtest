"""Python 기준 픽스처의 *입력*을 Go 테스트용 JSON으로 내보낸다 (go-migration 1단계).

develop의 두 특성화 테스트는 입력을 코드 안에서 만든다:
  - tests/unit/test_portfolio_manager_response_snapshot.py: 사인파 합성 시세(_frame), 환율(_fx_rates)
  - tests/e2e/test_golden_master.py: 요청 payload (시세는 tests/e2e/data/*.csv)
Go 쪽은 Python을 실행할 수 없으므로 같은 입력을 데이터로 고정해 둔다.

기대값(스냅샷/골든 JSON)은 이 스크립트가 만들지 않는다. develop 테스트가 그 기대값을 통과하는지는
이미지 빌드(--target test)가 확인하고, 기대값 파일은 원본을 그대로 복사한다.

buy&hold 시나리오만 내보낸다. strategy_* 시나리오는 backtesting.py 결과를 SimpleNamespace로
mock하므로 엔진 기준값으로 쓸 수 없다.

실행: scripts/export-python-reference.sh (Docker, --network none). 호스트에서 직접 실행하지 않는다.
"""
import json
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/tests/unit")

import test_portfolio_manager_response_snapshot as snap  # noqa: E402

OUT = Path(os.environ.get("EXPORT_OUT", "/out"))
SOURCE_COMMIT = os.environ.get("SOURCE_COMMIT", "unknown")


def _finite(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError(f"non-finite input value: {value!r}")
    return value


def _history(frame, currency: str) -> dict:
    return {
        "currency": currency,
        "bars": [
            {"date": ts.strftime("%Y-%m-%d"), "close": _finite(close)}
            for ts, close in frame["Close"].items()
        ],
    }


def export_snapshot_inputs() -> dict:
    captured = {}

    def capture(request, frames, currencies=None, rates=None):
        currencies = currencies or {symbol: "USD" for symbol in frames}
        captured["value"] = {
            "request": request.model_dump(mode="json"),
            "histories": {
                symbol: _history(frame, currencies[symbol]) for symbol, frame in frames.items()
            },
            "fx_rates": {
                currency: {day.isoformat(): _finite(rate) for day, rate in sorted(table.items())}
                for currency, table in (rates or {}).items()
            },
        }
        return None

    snap._run_buy_hold = capture  # 시나리오 람다는 호출 시점에 모듈 전역을 조회한다
    scenarios = {}
    for name, run in snap._scenarios().items():
        if not name.startswith("buy_hold_"):
            continue
        captured.clear()
        run()
        value = captured["value"]
        stock_symbols = [
            item["symbol"] for item in value["request"]["portfolio"] if item["asset_type"] == "stock"
        ]
        value["missing_symbols"] = [s for s in stock_symbols if s not in value["histories"]]
        scenarios[name] = value

    return {
        "_meta": {
            "source": "backtest_be_fast/tests/unit/test_portfolio_manager_response_snapshot.py",
            "source_commit": SOURCE_COMMIT,
            "expected": "portfolio_manager_response_snapshot.json (same directory)",
            "notes": [
                "histories에 없는 stock 종목(missing_symbols)은 데이터 로드 실패로 취급된다.",
                "fx_rates: KRW는 1 USD당 KRW(나눗셈), EUR는 1 EUR당 USD(곱셈).",
                "Python 기대값은 회귀 기록일 뿐 합격 기준이 아니다 (docs/go-migration-plan.md).",
            ],
        },
        "scenarios": scenarios,
    }


def export_golden_request() -> dict:
    # tests/e2e/test_golden_master.py::test_golden_master_backtest_dca 의 payload와 mock 조건
    return {
        "_meta": {
            "source": "backtest_be_fast/tests/e2e/test_golden_master.py",
            "source_commit": SOURCE_COMMIT,
            "prices": "AAPL.csv (same directory), currency USD",
            "fx": "mock: KRW 1300.0 (unused, USD only)",
            "supplemental": "mocked empty (benchmarks/news/exchange_rates)",
            "expected": "expected_dca_output.json (same directory), rel/abs tol 1e-6",
        },
        "request": {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 1000.0,
                    "investment_type": "dca",
                    "dca_frequency": "weekly_1",
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-02-28",
            "strategy": "buy_hold_strategy",
        },
    }


def _write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, allow_nan=False)
        f.write("\n")
    print(f"wrote {path}")


if __name__ == "__main__":
    _write(OUT / "snapshot" / "inputs.json", export_snapshot_inputs())
    _write(OUT / "golden" / "request.json", export_golden_request())
