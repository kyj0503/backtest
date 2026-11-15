"""POST /api/v1/backtest 요청 모델과 업무 규칙 검증 (Go internal/engine/request.go).

형태·형식 검증(pydantic 422 목록)은 app/schemas/schemas.py가 먼저 한다. 여기서는 그 뒤의 업무 규칙을
Go와 같은 순서·문구로 검사하고, 실패하면 422 {"detail": "문구"}다.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from . import schedule, strategy
from .errors import validation

MAX_PLANNED_USD = 1e12

_SEOUL = timezone(timedelta(hours=9))


def seoul_today() -> int:
    """'미래 종료일' 검사의 기준 날짜(한국 날짜). 서비스 사용자가 한국에 있다."""
    return datetime.now(_SEOUL).date().toordinal()


@dataclass
class Asset:
    symbol: str
    amount: Optional[float] = None
    total_amount: Optional[float] = None
    weight: Optional[float] = None
    investment_type: str = "lump_sum"
    dca_frequency: str = "monthly_1"
    asset_type: str = "stock"
    custom_name: Optional[str] = None

    @property
    def cash(self) -> bool:
        return self.asset_type == "cash"

    @property
    def dca(self) -> bool:
        return self.investment_type == "dca"

    def id(self, index: int) -> str:
        """응답 안에서 항목을 잇는 키. 주식은 심볼, 현금은 "표시이름__cash_요청순번"(F07)."""
        if self.cash:
            return f"{self.symbol}__cash_{index + 1}"
        return self.symbol

    def base(self) -> float:
        """회당(일시면 전체) 기준 금액: 적립이 아니면 total_amount, 다음 amount, 다음 weight."""
        if self.total_amount is not None and not self.dca:
            return self.total_amount
        if self.amount is not None:
            return self.amount
        return self.weight if self.weight is not None else 0.0


@dataclass
class Request:
    portfolio: List[Asset]
    start: int
    end: int
    strategy: str = strategy.BUY_HOLD
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    commission: float = 0.002
    rebalance_frequency: Optional[str] = None  # None이면 생략
    include_stock_data: bool = True
    include_volatility_events: bool = True
    include_exchange_rates: bool = True
    include_benchmarks: bool = True
    include_news: bool = True

    @property
    def buy_hold(self) -> bool:
        return self.strategy == strategy.BUY_HOLD

    def rebalance(self) -> str:
        """생략하면 buy&hold는 monthly_1, 기술 전략은 none."""
        if self.rebalance_frequency is not None:
            return self.rebalance_frequency
        return "monthly_1" if self.buy_hold else "none"

    def planned_budget(self, a: Asset) -> float:
        if a.total_amount is not None:
            return a.total_amount
        if a.dca and a.weight is None:
            return a.base() * (1 + len(schedule.dates(self.start, self.end, a.dca_frequency)))
        return a.base()


@dataclass
class Limits:
    min_period_days: int
    max_period_days: int
    max_items: int
    max_symbol_len: int
    today: int


def _bad_amount(v: Optional[float]) -> bool:
    if v is None:
        return False
    return math.isnan(v) or math.isinf(v) or v <= 0 or v > MAX_PLANNED_USD


def _bad_weight(v: Optional[float]) -> bool:
    if v is None:
        return False
    return math.isnan(v) or v < 0 or v > 100


def validate_symbol(symbol: str, cash: bool, max_len: int) -> None:
    n = len(symbol)
    if n == 0 or n > max_len:
        raise validation("유효하지 않은 종목 심볼입니다.")
    if not cash:
        for c in symbol:
            if not (("a" <= c <= "z") or ("A" <= c <= "Z") or ("0" <= c <= "9") or c in ".-"):
                raise validation("유효하지 않은 종목 심볼입니다.")


def validate_period(start: int, end: int, lim: Limits) -> None:
    days = end - start
    if days < lim.min_period_days or days > lim.max_period_days or end > lim.today:
        raise validation(
            f"조회 기간은 {lim.min_period_days}~{lim.max_period_days}일이며 종료일은 미래일 수 없습니다.")


def validate(r: Request, lim: Limits) -> None:
    """업무 규칙 검사. 주식 심볼을 대문자로 정규화한다(r을 바꾼다)."""
    validate_period(r.start, r.end, lim)
    if len(r.portfolio) == 0 or len(r.portfolio) > lim.max_items:
        raise validation(f"포트폴리오는 1~{lim.max_items}개 항목이어야 합니다.")
    if math.isnan(r.commission) or r.commission < 0 or r.commission >= 0.1:
        raise validation("수수료는 0 이상 0.1 미만이어야 합니다.")
    if not strategy.known(r.strategy):
        raise validation("지원하지 않는 전략입니다.")
    reb = r.rebalance()
    if reb != "none" and not schedule.known(reb):
        raise validation("유효하지 않은 리밸런싱 주기입니다.")
    seen = set()
    for a in r.portfolio:
        if a.asset_type not in ("cash", "stock") or a.investment_type not in ("lump_sum", "dca"):
            raise validation("유효하지 않은 자산 또는 투자 방식입니다.")
        validate_symbol(a.symbol, a.cash, lim.max_symbol_len)
        if not a.cash:
            a.symbol = a.symbol.upper()
            if a.symbol in seen:
                raise validation("중복된 종목입니다.")
            seen.add(a.symbol)
        if _bad_amount(a.amount) or _bad_amount(a.total_amount) or _bad_weight(a.weight):
            raise validation("금액 또는 비중이 유효하지 않습니다.")
        if a.amount is not None and a.weight is not None:
            raise validation("각 항목에 amount 또는 weight 중 하나를 입력해 주세요.")
        if a.total_amount is not None and (a.amount is None or a.weight is not None):
            raise validation("total_amount는 amount와 함께만 사용할 수 있습니다.")
        if not schedule.known(a.dca_frequency):
            raise validation("유효하지 않은 DCA 주기입니다.")
        if a.dca and len(schedule.dates(r.start, r.end, a.dca_frequency)) == 0:
            raise validation("DCA 주기가 백테스트 기간보다 깁니다.")
    planned = 0.0
    for a in r.portfolio:
        planned += r.planned_budget(a)
    if math.isnan(planned) or math.isinf(planned) or planned <= 0 or planned > MAX_PLANNED_USD:
        raise validation("총 예정 납입액은 0 초과 1조 USD 이하여야 합니다.")
    weights = amounts = False
    total = 0.0
    for a in r.portfolio:
        weights = weights or a.weight is not None
        amounts = amounts or a.amount is not None
        total += a.base()
    if weights and amounts:
        raise validation("금액과 비중을 혼합할 수 없습니다.")
    if weights and (total < 95 or total > 105):
        raise validation("비중 합계는 95~105%여야 합니다.")
    if not r.buy_hold:
        if r.rebalance() != "none" or any(a.dca for a in r.portfolio):
            raise validation("DCA와 리밸런싱은 buy_hold_strategy에서만 지원합니다.")
    strategy.parameters(r.strategy, r.strategy_params)
