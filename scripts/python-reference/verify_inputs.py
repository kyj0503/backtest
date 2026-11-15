"""내보낸 inputs.json만으로 Python 응답이 스냅샷과 같게 재현되는지 확인한다.

입력 JSON이 테스트 코드의 합성 데이터를 빠짐없이 담았다는 증거다. 통과하지 않으면 Go 테스트가
Python 기대값과 다른 입력을 보게 되므로 픽스처를 커밋하지 않는다.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, "/app/tests/unit")

import pandas as pd  # noqa: E402

import test_portfolio_manager_response_snapshot as snap  # noqa: E402
from app.schemas.schemas import PortfolioBacktestRequest  # noqa: E402

DIR = Path("/out/snapshot")


def main() -> None:
    inputs = json.loads((DIR / "inputs.json").read_text(encoding="utf-8"))["scenarios"]
    expected = json.loads((DIR / "portfolio_manager_response_snapshot.json").read_text(encoding="utf-8"))
    for name, case in inputs.items():
        frames = {
            symbol: pd.DataFrame(
                {"Close": [bar["close"] for bar in hist["bars"]]},
                index=pd.DatetimeIndex([bar["date"] for bar in hist["bars"]]),
            )
            for symbol, hist in case["histories"].items()
        }
        currencies = {symbol: hist["currency"] for symbol, hist in case["histories"].items()}
        rates = {
            cur: {dt.date.fromisoformat(day): rate for day, rate in table.items()}
            for cur, table in case["fx_rates"].items()
        }
        request = PortfolioBacktestRequest(**case["request"])
        actual = snap._to_client_json(
            snap._run_buy_hold(request, frames, currencies or None, rates or None)
        )
        snap._assert_same(actual, expected[name], name)
        print(f"ok {name}")


if __name__ == "__main__":
    main()
