import logging
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
        return price is not None and float(price) > 0
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
                # [P2-14] 정기 매수의 기준일(reference_date)을 "이론상 시작일"이
                # 아니라 "실제로 돈이 들어간 날"로 앵커링한다. 초기 매수가 지연된
                # 경우(예: 이 종목의 시장이 한동안 휴장) 이걸 빼먹으면
                # execute_periodic_purchases가 여전히 start_date_obj 기준으로
                # 이미 지나버린 정기 매수 목표일을 계산해, 지연된 초기 매수와
                # 같은 날 정기 매수까지 겹쳐 이중 집행될 수 있다.
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
        """
        주기적 DCA 투자를 실행합니다 (Nth Weekday 기반).

        **역할**:
        - 설정된 주기(weekly, biweekly, monthly 등)에 따라 자동 매수
        - Nth Weekday 방식으로 요일 패턴 유지
        - DCA 투자 횟수 제한 준수

        **파라미터**:
        - current_date: 현재 시뮬레이션 날짜
        - stock_amounts: 종목별 투자 금액
        - current_prices: 종목별 USD 변환 가격 (밸류에이션용, ffill 포함 가능)
        - dca_info: 종목 정보 (DcaStrategyInfo 모델)
        - shares: 종목별 보유 주식 수
        - commission: 거래 수수료
        - start_date_obj: 시뮬레이션 시작 날짜
        - tradeable_keys: [P2-14] 오늘 RAW 데이터로 실제 관측된 종목 집합.
          None이면(하위 호환) current_prices 유무만으로 판단한다. 값이 주어지면
          이 집합에 없는 종목은(current_prices에 ffill된 값이 있더라도) 오늘
          매수하지 않고 다음 관측일까지 대기한다.

        **반환**:
        - trades_executed: 실행된 거래 수
        - daily_cash_inflow: 당일 현금 유입 (투자 금액)

        **트리거 판정 방식 (레벨 기반)**:
        예전에는 "current >= next_dca_date AND prev < next_dca_date" 라는 엣지
        검출 방식을 썼다. 이 방식은 그 순간에 매수가 실제로 집행된다는 전제
        하에서만 안전하다 -- next_dca_date가 매수 성공 시에만 미래로 전진하기
        때문에, 만약 그 날 종목이 관측되지 않아 매수를 건너뛰면 prev/next
        관계가 다시는 "prev < next"를 만족하지 못해 그 회차가 영영 유실된다.
        [P2-14]에서 거래를 tradeable_keys로 게이팅하면 이 유실이 실제로
        발생하므로, "current >= next_dca_date" 레벨 조건만으로 판단하도록
        바꿨다. next_dca_date는 매수가 실제로 집행된 날에만 미래로 전진하므로
        (get_next_nth_weekday는 항상 기준일보다 엄격히 미래인 날짜를 반환),
        이 레벨 조건은 매수가 실행될 때까지 계속 참을 유지해 자동으로
        재시도되고, 실행되는 순간 즉시 거짓이 되어 같은 날 두 번 집행되지
        않는다.

        [P2-14] `original_nth_weekday`를 잠그는 조건에서 `last_dca_date is
        None`을 제거한 이유: 초기 매수(execute_initial_purchases)가 이제
        DCA 첫 회차에서도 last_dca_date를 설정하므로, 그 조건을 그대로 두면
        이 메서드가 처음 호출되는 시점에 이미 last_dca_date가 채워져 있어
        원본 Nth 값이 영영 잠기지 않는다 (매번 reference_date의 요일에서
        다시 계산되어, get_next_nth_weekday가 참조일 자체의 요일을 쓰는
        특성과 맞물려 스케줄이 표류할 수 있다). original_nth_weekday 자신의
        None 여부만으로 "아직 한 번도 잠기지 않았음"을 판단하는 것으로
        충분하다.
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

            # Nth Weekday 기반 DCA 실행
            dca_frequency = info.dca_frequency
            period_info = FREQUENCY_MAP.get(dca_frequency)

            if period_info is None:
                logger.error(f"{symbol}: 알 수 없는 DCA 주기 '{dca_frequency}'")
                continue

            period_type, interval = period_info

            # 첫 실행 시 original_nth 값 저장 (한 번 잠기면 이후 재계산하지
            # 않는다 -- last_dca_date는 이제 초기 매수 시점에도 설정될 수
            # 있으므로 이 조건에서 제외한다. original_nth_weekday 자체가
            # "아직 한 번도 잠기지 않았음"의 충분한 신호다).
            if info.original_nth_weekday is None:
                info.original_nth_weekday = get_weekday_occurrence(start_date_obj)
                logger.debug(f"{symbol}: 원본 Nth 값 설정 = {info.original_nth_weekday}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            # 다음 DCA 날짜 계산 (original_nth 유지, 마지막 "실제 집행일"에서부터)
            reference_date = info.last_dca_date or start_date_obj
            original_nth = info.original_nth_weekday
            next_dca_date = get_next_nth_weekday(reference_date, period_type, interval, original_nth)

            current_date_val = current_date.date() if isinstance(current_date, datetime) else current_date
            next_dca_date_val = next_dca_date.date() if isinstance(next_dca_date, datetime) else next_dca_date

            if current_date_val >= next_dca_date_val:
                # 투자 횟수 확인
                executed_count = info.executed_count

                if executed_count < info.dca_periods:
                    is_tradeable = tradeable_keys is None or symbol in tradeable_keys
                    has_valid_price = (
                        symbol in current_prices
                        and _is_tradeable_price(current_prices[symbol])
                    )
                    if has_valid_price and is_tradeable:
                        price = current_prices[symbol]
                        period_amount = info.monthly_amount  # 회당 투자 금액
                        invest_amount = period_amount * (1 - commission)
                        shares[symbol] += invest_amount / price
                        trades_executed += 1  # DCA 추가 매수 거래
                        daily_cash_inflow += period_amount  # DCA 추가 투자 유입 기록

                        # 실행 횟수 및 마지막 실행 날짜 업데이트
                        info.executed_count = executed_count + 1
                        info.last_dca_date = current_date_val # Use pre-converted value for consistency

                        # 다음 예정일 계산 (로그용)
                        next_scheduled = get_next_nth_weekday(current_date, period_type, interval, original_nth)
                        current_nth = get_weekday_occurrence(current_date)
                        logger.info(
                            f"{current_date.date()}: {symbol} DCA 추가 매수 실행! "
                            f"(주기 {info.executed_count}/{info.dca_periods}, "
                            f"금액: ${period_amount:,.2f}, "
                            f"실행: {current_nth}번째 {['월','화','수','목','금','토','일'][current_date.weekday()]}요일, "
                            f"다음 예정: {next_scheduled.date()})"
                        )
                    else:
                        # [P2-14] 예정일에 도달했지만 오늘 관측되지 않았다(또는
                        # 가격이 아예 없다). executed_count/last_dca_date를
                        # 갱신하지 않으므로 next_dca_date가 그대로 유지되어
                        # 다음 날에도 이 레벨 조건이 계속 참이 되고, 실제로
                        # 관측되는 날 자동으로 재시도된다 (회차 유실 없음).
                        logger.debug(
                            f"{current_date.date()}: {symbol} DCA 매수 예정일 도달했지만 "
                            f"당일 데이터 없음 (주기 {executed_count + 1}/{info.dca_periods}, 다음 거래일 재시도)"
                        )

        return trades_executed, daily_cash_inflow
