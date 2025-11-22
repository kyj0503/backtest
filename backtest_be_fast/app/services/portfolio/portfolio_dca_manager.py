"""DCA(Dollar Cost Averaging) 투자 관리

초기 매수 및 주기적 DCA 투자 실행을 담당합니다.
Nth Weekday 방식으로 DCA 일정을 관리합니다.
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, date
import pandas as pd

from app.schemas.schemas import FREQUENCY_MAP
from app.services.rebalance_helper import get_next_nth_weekday, get_weekday_occurrence

logger = logging.getLogger(__name__)


class PortfolioDcaManager:
    """DCA(Dollar Cost Averaging) 투자 관리 클래스"""

    def execute_initial_purchases(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        shares: Dict[str, float],
        commission: float
    ) -> Tuple[int, float]:
        """
        첫 날 초기 매수를 실행합니다 (일시불 또는 DCA 첫 투자).

        **역할**:
        - 일시불(lump_sum): 전액 한 번에 투자
        - DCA: 첫 달 금액만 투자

        **파라미터**:
        - current_date: 현재 시뮬레이션 날짜
        - stock_amounts: 종목별 투자 금액
        - current_prices: 종목별 USD 변환 가격
        - dca_info: 종목 정보 (투자 방식, 월별 금액)
        - shares: 종목별 보유 주식 수 (MODIFIED)
        - commission: 거래 수수료 (0.002 = 0.2%)

        **반환**:
        - trades_executed: 실행된 거래 수
        - daily_cash_inflow: 당일 현금 유입 (투자 금액)
        """
        trades_executed = 0
        daily_cash_inflow = 0.0

        for unique_key, amount in stock_amounts.items():
            symbol = dca_info[unique_key]['symbol']
            info = dca_info[unique_key]
            investment_type = info['investment_type']

            if unique_key not in current_prices:
                continue

            price = current_prices[unique_key]

            if investment_type == 'lump_sum':
                # 일시불: 목표 비중대로 전액 투자
                invest_amount = amount * (1 - commission)  # 수수료 차감
                shares[unique_key] = invest_amount / price
                trades_executed += 1  # 초기 매수 거래
                daily_cash_inflow += amount  # 일시불도 첫 날 유입
                logger.info(f"{current_date.date()}: {unique_key} 일시불 첫 투자 (금액: ${amount:,.2f}, 가격: ${price:.2f})")
            else:  # DCA
                # DCA 첫 달 투자
                monthly_amount = info['monthly_amount']
                invest_amount = monthly_amount * (1 - commission)
                shares[unique_key] = invest_amount / price
                trades_executed += 1  # 첫 DCA 매수 거래
                daily_cash_inflow += monthly_amount  # DCA 첫 투자 유입
                logger.info(f"{current_date.date()}: {unique_key} DCA 첫 투자 (금액: ${monthly_amount:,.2f}, interval_weeks: {info.get('interval_weeks', '?')})")

        return trades_executed, daily_cash_inflow

    def execute_periodic_purchases(
        self,
        current_date: pd.Timestamp,
        prev_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        shares: Dict[str, float],
        commission: float,
        start_date_obj: datetime
    ) -> Tuple[int, float]:
        """
        주기적 DCA 투자를 실행합니다 (Nth Weekday 기반).

        **역할**:
        - 설정된 주기(weekly, biweekly, monthly 등)에 따라 자동 매수
        - Nth Weekday 방식으로 요일 패턴 유지
        - DCA 투자 횟수 제한 준수

        **파라미터**:
        - current_date: 현재 시뮬레이션 날짜
        - prev_date: 이전 시뮬레이션 날짜
        - stock_amounts: 종목별 투자 금액
        - current_prices: 종목별 USD 변환 가격
        - dca_info: 종목 정보 (MODIFIED - executed_count, last_dca_date 업데이트)
        - shares: 종목별 보유 주식 수 (MODIFIED)
        - commission: 거래 수수료
        - start_date_obj: 시뮬레이션 시작 날짜

        **반환**:
        - trades_executed: 실행된 거래 수
        - daily_cash_inflow: 당일 현금 유입 (투자 금액)
        """
        trades_executed = 0
        daily_cash_inflow = 0.0

        for symbol, _ in stock_amounts.items():
            if symbol not in dca_info:
                logger.error(f"DCA 정보 없음: {symbol}")
                continue

            info = dca_info[symbol]
            if info['investment_type'] != 'dca':
                continue

            # Nth Weekday 기반 DCA 실행
            dca_frequency = info['dca_frequency']
            period_info = FREQUENCY_MAP.get(dca_frequency)

            if period_info is None:
                logger.error(f"{symbol}: 알 수 없는 DCA 주기 '{dca_frequency}'")
                continue

            period_type, interval = period_info

            # 첫 실행 시 original_nth 값 저장
            if info['original_nth_weekday'] is None and info.get('last_dca_date') is None:
                info['original_nth_weekday'] = get_weekday_occurrence(start_date_obj)
                logger.debug(f"{symbol}: 원본 Nth 값 설정 = {info['original_nth_weekday']}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            # 다음 DCA 날짜 계산 (original_nth 유지)
            reference_date = info.get('last_dca_date') or start_date_obj
            original_nth = info.get('original_nth_weekday')
            next_dca_date = get_next_nth_weekday(reference_date, period_type, interval, original_nth)

            # 현재 날짜가 DCA 실행일인지 확인 (경계 조건: current >= next AND prev < next)
            if current_date >= next_dca_date and prev_date < next_dca_date:
                # 투자 횟수 확인
                executed_count = info.get('executed_count', 0)

                if executed_count < info['dca_periods']:
                    if symbol in current_prices:
                        price = current_prices[symbol]
                        period_amount = info['monthly_amount']  # 회당 투자 금액
                        invest_amount = period_amount * (1 - commission)
                        shares[symbol] += invest_amount / price
                        trades_executed += 1  # DCA 추가 매수 거래
                        daily_cash_inflow += period_amount  # DCA 추가 투자 유입 기록

                        # 실행 횟수 및 마지막 실행 날짜 업데이트
                        info['executed_count'] = executed_count + 1
                        info['last_dca_date'] = current_date

                        # 다음 예정일 계산 (로그용)
                        next_scheduled = get_next_nth_weekday(current_date, period_type, interval, original_nth)
                        current_nth = get_weekday_occurrence(current_date)
                        logger.info(
                            f"{current_date.date()}: {symbol} DCA 추가 매수 실행! "
                            f"(주기 {executed_count + 1}/{info['dca_periods']}, "
                            f"금액: ${period_amount:,.2f}, "
                            f"실행: {current_nth}번째 {['월','화','수','목','금','토','일'][current_date.weekday()]}요일, "
                            f"다음 예정: {next_scheduled.date()})"
                        )
                    else:
                        logger.warning(f"{current_date.date()}: {symbol} DCA 매수 시점이지만 가격 데이터 없음 (주기 {executed_count + 1}/{info['dca_periods']})")

        return trades_executed, daily_cash_inflow
