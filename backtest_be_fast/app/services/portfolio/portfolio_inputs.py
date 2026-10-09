"""포트폴리오 요청 입력 변환 (요청 → 종목별 투자 금액·DCA 정보)

PortfolioManagerService의 두 경로가 요청을 시뮬레이션 입력으로 바꾸는 규칙을 모은다.

- weight → 금액 환산(`weight_to_amount`)은 두 경로가 같은 규칙을 쓴다.
- 금액/비중 모드 판정은 경로마다 다르다(아래 각 함수 docstring). 스키마가
  amount·weight 혼합은 막지만 "비중 합계 95~105%를 만족하면서 일부 종목만 둘 다
  비운" 요청은 통과시키므로, 그 경우 두 경로가 서로 다른 메시지로 거부한다.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd

from app.core.exceptions import ValidationError
from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.schemas import FREQUENCY_MAP
from app.services.rebalance_helper import generate_periodic_schedule

logger = logging.getLogger(__name__)

# weight 모드의 환산 기준 원금. 비중(%)을 이 금액에 대한 비율로 본다.
WEIGHT_BASE_AMOUNT = 100.0


def weight_to_amount(weight: float) -> float:
    """비중(%)을 100 단위 기준 금액으로 환산한다 (전략·buy&hold 공통 규칙).

    총액을 100으로 하드코딩하지 않고 환산된 금액의 합을 분모로 써야 비중 합계가
    100%가 아닐 때(스키마 허용 95~105%) 수익률 분모가 실제 원금과 맞는다 (P1-03).
    """
    return WEIGHT_BASE_AMOUNT * (weight / 100.0)


# ---------------------------------------------------------------------------
# 전략 경로
# ---------------------------------------------------------------------------

def strategy_asset_key(item, index: int, portfolio) -> str:
    """중복 현금 이름만 구분하고 나머지 응답 키는 유지한다."""
    if item.asset_type != 'cash' or sum(entry.symbol == item.symbol for entry in portfolio) == 1:
        return item.symbol
    key = f"{item.symbol}__cash_{index + 1}"
    names = {entry.symbol for entry in portfolio}
    while key in names:
        key += '_'
    return key


def resolve_strategy_amounts(portfolio) -> Tuple[Dict[str, float], float]:
    """전략 경로의 종목별 금액과 총 투자금을 구한다.

    포트폴리오 전체가 amount 모드이거나 전체가 weight 모드여야 한다(하나라도
    둘 다 비었으면 거부). 중복 현금 이름에는 입력 순서를 붙인다.
    """
    if all(item.amount is not None for item in portfolio):
        amounts = {strategy_asset_key(item, i, portfolio): item.amount for i, item in enumerate(portfolio)}
    elif all(item.weight is not None for item in portfolio):
        amounts = {strategy_asset_key(item, i, portfolio): weight_to_amount(item.weight)
                   for i, item in enumerate(portfolio)}
    else:
        raise ValidationError('포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다.')
    return amounts, sum(amounts.values())


# ---------------------------------------------------------------------------
# buy&hold 경로
# ---------------------------------------------------------------------------

def count_dca_periods(investment_type: str, dca_frequency: str,
                      start_date_obj: datetime, end_date_obj: datetime) -> int:
    """DCA 투자 횟수 (Nth Weekday 방식). 일시불이면 1.

    시뮬레이션이 실제로 매수하는 날짜를 그대로 생성해서 센다. 과거에는
    "월 = 30일" 근사로 추정했는데, 이 값이 총 투자금(= 수익률의 분모)이 되기
    때문에 실제 집행 횟수와 어긋나면 집행되지 않은 납입금이 손실로 보고됐다.
    (2024년 전체·월간 기준 13회로 추정되지만 실제로는 12회 → -7.69%)
    """
    if investment_type != 'dca':
        return 1
    period_type, interval = FREQUENCY_MAP.get(dca_frequency, FREQUENCY_MAP['monthly_1'])
    # 초회 매수 1회 + 이후 정기 매수 예정일 수
    periodic_dates = generate_periodic_schedule(
        start_date=start_date_obj,
        end_date=end_date_obj,
        period_type=period_type,
        interval=interval,
    )
    return 1 + len(periodic_dates)


@dataclass
class BuyHoldAllocation:
    """buy&hold 시뮬레이션 입력.

    amounts: unique_key → 실제 총 투자 금액 (DCA는 회당 금액 × 횟수)
    dca_info: unique_key → DcaStrategyInfo
    cash_amount: 현금 자산 합계
    symbols_to_load: 가격을 로드할 주식 심볼 (요청 순서)
    """
    amounts: Dict[str, float] = field(default_factory=dict)
    dca_info: Dict[str, DcaStrategyInfo] = field(default_factory=dict)
    cash_amount: float = 0
    symbols_to_load: List[str] = field(default_factory=list)


class BuyHoldAllocationBuilder:
    """요청 항목을 하나씩 받아 BuyHoldAllocation을 만든다.

    항목 단위로 받는 이유: 호출자가 항목마다 부가 작업(티커 인기 메트릭)을 하다
    중간 항목에서 거부될 때, 그 앞 항목까지만 처리된 기존 순서를 그대로 지킨다.
    """

    def __init__(self, start_date_obj: datetime, end_date_obj: datetime):
        self.start_date_obj = start_date_obj
        self.end_date_obj = end_date_obj
        self.allocation = BuyHoldAllocation()
        # 현금 항목은 심볼 중복이 허용되므로 고유 키가 필요하다 (P2-07)
        self._cash_entry_counter = 0

    def add(self, item) -> None:
        allocation = self.allocation
        symbol = item.symbol
        investment_type = getattr(item, 'investment_type', 'lump_sum')
        dca_frequency = getattr(item, 'dca_frequency', 'monthly_1')
        dca_periods = count_dca_periods(
            investment_type, dca_frequency, self.start_date_obj, self.end_date_obj
        )
        asset_type = getattr(item, 'asset_type', 'stock')

        # amount 또는 weight 기반으로 회당 투자 금액 계산
        if item.amount is not None:
            per_period_amount = item.amount  # 입력한 금액 = 회당 투자 금액
        elif item.weight is not None:
            # weight 모드: 전략 경로와 같은 weight_to_amount로 총 투자금액을 환산한다
            # (수정 전에는 여기서 0으로 고정되어 total_amount가 0이 되고 시뮬레이션
            # 정규화 단계에서 0으로 나누기가 발생했다 - P1-04). DCA는 이 환산 총액을
            # dca_periods로 나눠 회당 금액을 구해야, 아래의
            # "total_investment = per_period_amount * dca_periods"가 환산 총액과 다시 일치한다.
            weight_based_total = weight_to_amount(item.weight)
            per_period_amount = (
                weight_based_total / dca_periods if investment_type == 'dca'
                else weight_based_total
            )
        else:
            raise ValidationError('포트폴리오 내 모든 종목은 amount 또는 weight를 입력해야 합니다.')

        # 총 투자 금액: 분할 매수는 회당 금액 × 횟수, 일시불은 회당 금액 = 총 금액
        if investment_type == 'dca':
            total_investment = per_period_amount * dca_periods
        else:
            total_investment = per_period_amount

        # 고유 키: 현금 자산은 schemas.py의 validate_portfolio가 중복 검증에서
        # 의도적으로 제외하므로(같은 이름의 현금을 여러 개 추가할 수 있음) symbol을
        # 그대로 키로 쓰면 먼저 들어온 항목이 나중 항목에 덮어써져 total_amount와
        # cash_amount가 어긋난다 (P2-07). 주식 심볼은 스키마가 이미 중복을 거부하므로
        # symbol을 그대로 키로 쓰고, 이후 코드가 dca_info[unique_key].symbol로
        # 역참조하는 구조와도 맞는다.
        if asset_type == 'cash':
            self._cash_entry_counter += 1
            unique_key = f"{symbol}__cash_{self._cash_entry_counter}"
        else:
            unique_key = symbol

        allocation.amounts[unique_key] = total_investment
        allocation.dca_info[unique_key] = DcaStrategyInfo(
            symbol=symbol,
            allocation=0.0,  # Will be calculated if needed, or derived from amounts
            asset_type=asset_type,
            investment_type=investment_type,
            monthly_amount=per_period_amount,
            dca_frequency=dca_frequency,
            dca_periods=dca_periods
        )

        if asset_type == 'cash':
            allocation.cash_amount += total_investment
            logger.info(f"현금 자산 {symbol} 추가 (금액: ${total_investment:,.2f})")
            return

        logger.info(f"종목 {symbol} 데이터 로드 예정 (총 투자금액: ${total_investment:,.2f}, 방식: {investment_type})")
        if investment_type == 'dca':
            logger.info(f"분할 매수: {dca_periods}회에 걸쳐 회당 ${per_period_amount:,.2f}씩 (총 ${total_investment:,.2f})")
            logger.info(f"DCA 설정: frequency={dca_frequency}, dca_periods={dca_periods}")

        allocation.symbols_to_load.append(symbol)


def drop_unloaded_symbols(allocation: BuyHoldAllocation,
                          portfolio_data: Dict[str, pd.DataFrame]) -> List[str]:
    """가격 데이터를 불러오지 못한 종목을 분모와 시뮬레이션에서 빼고 경고를 돌려준다 (A-03).

    data_loader는 로드 실패·빈 결과 종목을 로그만 남기고 버린다. 과거에는 그
    종목의 금액이 amounts에 남아 total_amount(= 수익률의 분모)에 포함됐는데, 가격
    시리즈가 없어 매수도 현금 계상도 되지 않아 투자금이 증발한 것처럼 수익률이
    과소보고됐다(AAPL + 없는 종목 반반 → 0.96%). allocation을 제자리에서 고친다.
    """
    warnings = []
    failed_keys = [
        key for key, info in allocation.dca_info.items()
        if info.asset_type != 'cash' and info.symbol not in portfolio_data
    ]
    for key in failed_keys:
        warnings.append(
            f"종목 {allocation.dca_info[key].symbol}의 가격 데이터를 불러오지 못해 백테스트에서 "
            f"제외했습니다 (투자금 ${allocation.amounts[key]:,.2f}는 수익률 계산에 포함되지 않음)."
        )
        del allocation.amounts[key]
        del allocation.dca_info[key]
    return warnings
