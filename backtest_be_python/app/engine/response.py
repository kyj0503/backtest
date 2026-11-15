"""응답 조립·직렬화 (Go internal/engine/response.go, jsonenc.go).

응답은 키 순서를 지키는 dict로 만든다. 직렬화는 FastAPI JSONResponse와 같은 형식
(UTF-8 그대로, 구분자 공백 없음)이고, 유한수가 아닌 값이 있으면 500이다(Go와 같다).
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from . import civil

ASSUMPTIONS = {
    "quantity_unit": "fractional_adjusted_unit",
    "account_currency": "USD",
    "weight_basis": "asset_account_including_uninvested_cash",
    "price_basis": "adjusted_total_return",
}

# POST include_*가 붙이는 키의 순서(Python unified_data_service).
SUPPLEMENTAL_KEYS = ["ticker_info", "stock_data", "exchange_rates", "exchange_stats", "volatility_events",
                     "sp500_benchmark", "nasdaq_benchmark", "latest_news", "supplemental_status"]


def curves(start: int, equity: List[float], returns: List[float]) -> Tuple[Dict[str, float], Dict[str, float]]:
    """equity_curve(USD)와 daily_returns(%)."""
    keys = civil.date_keys(start, len(equity))
    return dict(zip(keys, equity)), {k: r * 100 for k, r in zip(keys, returns)}


def encode(content: Any) -> bytes:
    """Starlette JSONResponse.render와 같은 형식. NaN·Inf는 ValueError."""
    return json.dumps(content, ensure_ascii=False, allow_nan=False, indent=None,
                      separators=(",", ":")).encode("utf-8")
