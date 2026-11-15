import logging
import math
from typing import Dict, Optional, Set, Tuple
from datetime import datetime, date
import pandas as pd

from app.schemas.schemas import FREQUENCY_MAP
from app.services.rebalance_helper import get_next_nth_weekday, get_weekday_occurrence
from app.domain.portfolio_domain import DcaStrategyInfo

logger = logging.getLogger(__name__)


def _is_tradeable_price(price) -> bool:
    """체결에 쓸 수 있는 가격인지 확인한다.

    0이면 주식 수 계산에서 ZeroDivisionError가 나고, 음수면 조용히 음수
    주식 수가 만들어진다. 둘 다 데이터 품질 문제이므로 체결하지 않는다.
    NaN도 같은 이유로 배제한다 (NaN과의 비교는 항상 False).
    """
    try:
        return price is not None and math.isfinite(float(price)) and float(price) > 0
    except (TypeError, ValueError):
        return False


class PortfolioDcaManager:
    """DCA(Dollar Cost Averaging) 투자 관리 클래스"""

    def execute_initial_purchases(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, DcaStrategyInfo],
        shares: Dict[str, float],
        commission: float,
        pending_keys: Optional[Set[str]] = None,
        tradeable_keys: Optional[Set[str]] = None
    ) -> Tuple[int, float]:
        """
        초기 매수를 실행합니다 (일시불 또는 DCA 첫 투자).

        **역할**:
        - 일시불(lump_sum): 전액 한 번에 투자
        - DCA: 첫 달 금액만 투자

        **파라미터**:
        - current_date: 현재 시뮬레이션 날짜
        - stock_amounts: 종목별 투자 금액 (pending_keys가 주어지면 그 종목만 대상)
        - current_prices: 종목별 USD 변환 가격 (밸류에이션용, ffill 포함 가능)
        - dca_info: 종목 정보 (DcaStrategyInfo 모델)
        - shares: 종목별 보유 주식 수
        - commission: 거래 수수료 (0.002 = 0.2%)
        - pending_keys: 아직 초기 매수가 이뤄지지 않은 종목 집합.
          매수에 성공한 종목은 이 집합에서 제거된다. 첫날 가격이 없는 종목
          (예: 한쪽 시장 휴장일에 시작)은 집합에 남아 다음 거래일에 재시도된다.
        - tradeable_keys: [P2-14] 오늘 RAW 데이터로 실제 관측된 종목 집합.
          None이면(하위 호환) current_prices 유무만으로 판단한다. 값이 주어지면
          current_prices에 값이 있어도(ffill로 채워진 값일 수 있음) 이 집합에
          없는 종목은 매수하지 않는다 -- 초기 매수는 애초에 "이전에 한 번도
          관측되지 않은" 종목만 대상이므로 ffill이 그 이전 시점의 값을
          만들어낼 수 없어 current_prices 단독 체크와 결과는 대개 같지만,
          다른 거래 함수들과 판단 근거를 통일해 명시적으로 만든다.

        **반환**:
        - trades_executed: 실행된 거래 수
        - daily_cash_inflow: 당일 현금 유입 (투자 금액)
        """
        if pending_keys is not None:
            stock_amounts = {
                key: amount for key, amount in stock_amounts.items() if key in pending_keys
            }
        trades_executed = 0
        daily_cash_inflow = 0.0

        for unique_key, amount in stock_amounts.items():
            if unique_key not in dca_info:
                continue

            info = dca_info[unique_key]

            investment_type = info.investment_type

            if unique_key not in current_prices:
                # 이 종목은 아직 가격이 없다 (예: 다른 시장의 휴장일에 시작).
                # pending_keys에 남겨 두면 호출자가 다음 날 다시 시도한다.
                continue

            if tradeable_keys is not None and unique_key not in tradeable_keys:
                # [P2-14] current_prices에는 값이 있지만(이론상 ffill 잔재) 오늘
                # 실제로 관측되지는 않았다. 존재하지 않았던 가격에 체결시키지
                # 않도록 재시도 대상(pending_keys)에 그대로 남겨 둔다.
                continue

            price = current_prices[unique_key]

            if not _is_tradeable_price(price):
                # 가격 0은 ZeroDivisionError를, 음수는 음수 주식 수를 만든다.
                # 데이터 품질 문제이므로 체결하지 않고 재시도 대상으로 남긴다.
                logger.warning(
                    f"{current_date.date()}: {unique_key} 초기 매수 건너뜀 "
                    f"(유효하지 않은 가격: {price})"
                )
                continue

            if investment_type == 'lump_sum':
                # 일시불: 목표 비중대로 전액 투자
                invest_amount = amount * (1 - commission)  # 수수료 차감
                shares[unique_key] = invest_amount / price
                trades_executed += 1  # 초기 매수 거래
                daily_cash_inflow += amount  # 일시불도 첫 날 유입
                logger.info(f"{current_date.date()}: {unique_key} 일시불 첫 투자 (금액: ${amount:,.2f}, 가격: ${price:.2f})")
            else:  # DCA
                # DCA 첫 달 투자
                monthly_amount = info.monthly_amount
                invest_amount = monthly_amount * (1 - commission)
                shares[unique_key] = invest_amount / price
                trades_executed += 1  # 첫 DCA 매수 거래
                daily_cash_inflow += monthly_amount  # DCA 첫 투자 유입
                # 초회 매수도 납입 1회로 계상한다. dca_periods가 "총 납입 횟수"
                # (초회 포함)이므로, 이렇게 해야 정기 매수가 남은 횟수만 집행한다.
                info.executed_count = 1
                current_date_val = current_date.date() if isinstance(current_date, datetime) else current_date
                info.last_dca_date = current_date_val
                logger.info(f"{current_date.date()}: {unique_key} DCA 첫 투자 (금액: ${monthly_amount:,.2f}, interval_weeks: {info.dca_frequency})")

            if pending_keys is not None:
                pending_keys.discard(unique_key)

        return trades_executed, daily_cash_inflow

    def execute_periodic_purchases(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, DcaStrategyInfo],
        shares: Dict[str, float],
        commission: float,
        start_date_obj: datetime,
        tradeable_keys: Optional[Set[str]] = None
    ) -> Tuple[int, float]:
        """Execute due contributions on observed quotes, retaining the planned calendar.

        Missing quotes defer funding until a real execution. A contribution with
        no execution before the end is not invested capital and is not a loss.
        """
        trades_executed = 0
        daily_cash_inflow = 0.0

        for symbol, _ in stock_amounts.items():
            if symbol not in dca_info:
                logger.error(f"DCA 정보 없음: {symbol}")
                continue

            info = dca_info[symbol]
            if info.investment_type != 'dca':
                continue

            if info.executed_count == 0 or info.executed_count >= info.dca_periods:
                continue
            current = current_date.date() if isinstance(current_date, datetime) else current_date
            # Never double-fund an initial purchase on its deferred execution day.
            if info.last_dca_date == current:
                continue
            period_type, interval = FREQUENCY_MAP[info.dca_frequency]
            if info.original_nth_weekday is None:
                info.original_nth_weekday = get_weekday_occurrence(start_date_obj)
            if info.next_scheduled_date is None:
                planned = start_date_obj
                for _ in range(info.executed_count):
                    planned = get_next_nth_weekday(planned, period_type, interval, info.original_nth_weekday)
                info.next_scheduled_date = planned.date()
            if current < info.next_scheduled_date:
                continue
            if (tradeable_keys is not None and symbol not in tradeable_keys) or not _is_tradeable_price(current_prices.get(symbol)):
                continue
            # Catch up overdue scheduled contributions at the first real quote.
            # Advance the planned cursor, never the holiday-shifted trade date.
            while info.executed_count < info.dca_periods and current >= info.next_scheduled_date:
                amount = info.monthly_amount
                shares[symbol] += amount * (1 - commission) / current_prices[symbol]
                trades_executed += 1
                daily_cash_inflow += amount
                info.executed_count += 1
                info.last_dca_date = current
                planned = datetime.combine(info.next_scheduled_date, datetime.min.time())
                info.next_scheduled_date = get_next_nth_weekday(
                    planned, period_type, interval, info.original_nth_weekday).date()

        return trades_executed, daily_cash_inflow
