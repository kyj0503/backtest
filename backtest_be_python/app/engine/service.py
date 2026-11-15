"""POST /api/v1/backtest 계산 진입점 (Go internal/api/backtest.go compute + internal/engine/run.go).

흐름: pydantic 검증을 통과한 요청 → to_request(업무 규칙 검증, 실패 시 422 문자열) → 슬롯 획득 후
compute(시세 로드 + 계산) → supplemental 부가 데이터 → 응답 JSON.
"""
from __future__ import annotations

import copy
import logging
import math
import time
from datetime import datetime
from typing import Any, Dict

from fastapi.responses import Response

from ..core.config import settings
from . import buyhold, strategy, technical
from .errors import validation
from .marketdata import is_fx, valid_prices, valid_rate
from .request import Asset, Limits, Request, seoul_today, validate
from .response import encode
from .source import source
from .stats import finalize
from .supplemental import attach

logger = logging.getLogger(__name__)


def limits() -> Limits:
    return Limits(
        min_period_days=settings.min_backtest_period_days,
        max_period_days=settings.max_backtest_duration_days,
        max_items=settings.max_portfolio_items,
        max_symbol_len=settings.max_symbol_length,
        today=seoul_today(),
    )


def _ordinal(s: str) -> int:
    return datetime.strptime(s, "%Y-%m-%d").date().toordinal()


def to_request(model) -> Request:
    """pydantic PortfolioBacktestRequest → 엔진 요청. 업무 규칙을 검사한다(Go parseBacktest 뒷부분)."""
    portfolio = []
    for item in model.portfolio:
        portfolio.append(Asset(
            symbol=item.symbol,
            amount=item.amount,
            total_amount=item.total_amount,
            weight=item.weight,
            investment_type=item.investment_type,
            dca_frequency=item.dca_frequency,
            asset_type=item.asset_type,
            custom_name=item.custom_name,
        ))
    req = Request(
        portfolio=portfolio,
        start=_ordinal(model.start_date),
        end=_ordinal(model.end_date),
        strategy=model.strategy,
        strategy_params=dict(model.strategy_params or {}),
        commission=float(model.commission),
        rebalance_frequency=model.rebalance_frequency if "rebalance_frequency" in model.model_fields_set else None,
        include_stock_data=model.include_stock_data,
        include_volatility_events=model.include_volatility_events,
        include_exchange_rates=model.include_exchange_rates,
        include_benchmarks=model.include_benchmarks,
        include_news=model.include_news,
    )
    lim = limits()
    days = req.end - req.start
    if days < lim.min_period_days:
        raise validation(f"백테스트 기간이 너무 짧습니다: {days}일 (최소 {lim.min_period_days}일 필요)")
    try:
        validate(req, lim)
    except Exception:
        if not req.buy_hold:
            try:
                strategy.parameters(req.strategy, req.strategy_params)
            except Exception:
                # Python은 잘못된 전략 파라미터를 종목별 실패로 처리해 이 문구를 돌려줬다.
                raise validation("[ValidationError] 모든 종목의 백테스트가 실패했습니다.")
        raise
    return req


def run(req: Request, data) -> Dict[str, Any]:
    """검증된 요청과 시세로 계산한다(Go engine.Run). req는 복사본으로 다시 검증한다."""
    req = copy.deepcopy(req)
    validate(req, limits())
    # 거래 대상 시세는 체결 가능한 OHLC여야 한다. 환산에만 쓰는 환율은 일별 기준값(종가)만 본다(T02).
    traded = {a.symbol for a in req.portfolio if not a.cash}
    for symbol, h in data.items():
        conversion_only = is_fx(symbol) and symbol not in traded
        for b in h.bars:
            if (conversion_only and not valid_rate(b)) or (not conversion_only and not valid_prices(b)):
                raise validation("유효하지 않은 가격 데이터입니다.")
    d = buyhold.run(req, data) if req.buy_hold else technical.run(req, data)
    s = d["portfolio_statistics"]
    for k in ("Initial_Value", "Final_Value", "Total_Return", "Annual_Return", "Annual_Volatility"):
        v = s[k]
        if math.isnan(v) or math.isinf(v):
            raise validation("계산 결과가 지원하는 숫자 범위를 초과했습니다.")
    return d


def compute(req: Request) -> Response:
    """시세 로드 → 계산 → 부가 데이터 → JSON 응답."""
    from ..monitoring.custom_metrics import (BACKTEST_EXECUTION_TOTAL, BACKTEST_PROCESSING_SECONDS,
                                             observe_stage, record_ticker_popularity)

    symbols = [a.symbol for a in req.portfolio if not a.cash]
    for s in symbols:
        record_ticker_popularity(s)
    began = time.perf_counter()
    try:
        loaded = source.load(symbols, req.start, req.end)
        data = run(req, loaded.histories)
    except Exception:
        BACKTEST_EXECUTION_TOTAL.labels(strategy_type=req.strategy, status="error").inc()
        raise
    finally:
        observe_stage("simulation", time.perf_counter() - began)
    BACKTEST_EXECUTION_TOTAL.labels(strategy_type=req.strategy, status="success").inc()
    BACKTEST_PROCESSING_SECONDS.labels(strategy_type=req.strategy).observe(time.perf_counter() - began)
    attach(req, data, loaded.histories)
    data["portfolio_statistics"] = finalize(data["portfolio_statistics"])
    try:
        body = encode({"status": "success", "data": data})
        status = 200
    except (ValueError, TypeError) as e:
        logger.error("response encoding failed: %s", e)
        body = encode({"detail": "내부 서버 오류가 발생했습니다."})
        status = 500
    return Response(content=body, status_code=status, media_type="application/json")
