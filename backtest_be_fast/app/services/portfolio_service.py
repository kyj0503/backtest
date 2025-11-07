"""
포트폴리오 백테스트 서비스

**역할**:
- 여러 종목으로 구성된 포트폴리오의 백테스트 실행
- 분할 매수(DCA) 전략 지원
- 리밸런싱 로직 구현
- 포트폴리오 수익률 및 통계 계산

**통화 정책**:
- 개별 종목 가격: DB에 원래 통화로 저장 (KRW, JPY, EUR, GBP 등)
- 백테스트 연산: 모든 가격을 USD로 변환하여 계산
- 환율 변환: 13개 주요 통화 지원
  * 직접 환율: KRW=X, JPY=X, CNY=X 등 (1 USD = X 통화)
  * USD 환율: EURUSD=X, GBPUSD=X 등 (1 통화 = X USD)
- 프론트엔드 표시:
  * 개별 종목 시장 데이터(주가, 급등락) → 원래 통화
  * 백테스트 결과(리밸런싱, 수수료) → USD

**주요 기능**:
1. run_portfolio_backtest(): 메인 백테스트 실행 메서드
   - 단일 종목 → backtest_service로 위임
   - 다중 종목 → 전략에 따라 분기
2. run_buy_and_hold_portfolio_backtest(): Buy & Hold 전략 백테스트
3. run_strategy_portfolio_backtest(): 기술적 전략 백테스트
4. calculate_dca_portfolio_returns(): DCA 투자 수익률 계산
5. calculate_portfolio_statistics(): 샤프 비율, 최대 낙폭 등 통계

**지원 투자 방식**:
- lump_sum: 일시불 투자 (전액 한 번에 투자)
- dca: 분할 매수 (Dollar Cost Averaging, 정기적으로 나누어 투자)

**리밸런싱**:
- 주기적으로 포트폴리오 비중을 원래대로 조정
- 지원 주기: monthly, quarterly, annually, none

**의존성**:
- app/services/backtest_service.py: 단일 종목 백테스트
- app/services/yfinance_db.py: 주가 데이터 로딩
- app/repositories/backtest_repository.py: 백테스트 결과 저장

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (API 엔드포인트)
- Frontend: src/features/backtest/components/PortfolioForm.tsx (포트폴리오 설정)
- Frontend: src/features/backtest/hooks/useBacktestForm.ts (폼 상태 관리)

**통계 지표**:
- 총 수익률, 연환산 수익률
- 샤프 비율: 위험 대비 수익률
- 최대 낙폭(Max Drawdown): 최고점 대비 최대 하락폭
- 승률, 평균 수익/손실
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import logging
from decimal import Decimal

from app.schemas.schemas import PortfolioBacktestRequest, PortfolioStock
from app.schemas.requests import BacktestRequest
from app.services.yfinance_db import load_ticker_data, get_ticker_info_from_db
from app.services.backtest_service import backtest_service
from app.utils.serializers import recursive_serialize
from app.core.exceptions import (
    DataNotFoundError,
    InvalidSymbolError,
    ValidationError
)
from app.core.config import settings

logger = logging.getLogger(__name__)

# 환율 데이터 검색 설정
EXCHANGE_RATE_LOOKBACK_DAYS = 30  # 환율 데이터 누락 시 과거 검색 일수

# 지원하는 통화 및 환율 티커 매핑
SUPPORTED_CURRENCIES = {
    'USD': None,  # 기준 통화, 변환 불필요
    'KRW': 'KRW=X',  # 원화
    'JPY': 'JPY=X',  # 엔화
    'EUR': 'EURUSD=X',  # 유로
    'GBP': 'GBPUSD=X',  # 파운드
    'CNY': 'CNY=X',  # 위안화
    'HKD': 'HKD=X',  # 홍콩달러
    'TWD': 'TWD=X',  # 대만달러
    'SGD': 'SGD=X',  # 싱가포르달러
    'AUD': 'AUDUSD=X',  # 호주달러
    'CAD': 'CADUSD=X',  # 캐나다달러
    'CHF': 'CHFUSD=X',  # 스위스프랑
    'INR': 'INR=X',  # 루피
}

class DCACalculator:
    """분할 매수(DCA) 계산 유틸리티"""
    
    @staticmethod
    def calculate_dca_shares_and_return(df: pd.DataFrame, monthly_amount: float,
                                      dca_periods: int, start_date: str) -> Tuple[float, float, float, List[Dict]]:
        """
        DCA 투자의 총 주식 수량과 평균 단가, 수익률, 매수 로그를 계산

        Returns:
            (total_shares, average_price, return_rate, trade_log)
        """
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        total_shares = 0
        total_invested = 0
        trade_log = []  # DCA 매수 기록

        for month in range(dca_periods):
            # Use relativedelta for accurate calendar month arithmetic.
            investment_date = start_date_obj + relativedelta(months=month)
            month_price_data = df[df.index.date >= investment_date.date()]

            if not month_price_data.empty:
                month_price = month_price_data['Close'].iloc[0]
                actual_date = month_price_data.index[0]
                shares_bought = monthly_amount / month_price
                total_shares += shares_bought
                total_invested += monthly_amount

                # DCA 매수 기록 추가
                trade_log.append({
                    'EntryTime': actual_date.isoformat(),
                    'EntryPrice': float(month_price),
                    'Size': float(shares_bought),
                    'ExitTime': None,  # DCA는 매수만 있고 매도 없음
                    'ExitPrice': None,
                    'PnL': None,
                    'ReturnPct': None,
                    'Duration': None,
                })

        if total_shares > 0:
            average_price = total_invested / total_shares
            end_price = df['Close'].iloc[-1]
            return_rate = (end_price / average_price - 1) * 100
            return total_shares, average_price, return_rate, trade_log

        return 0, 0, 0, []

class RebalanceHelper:
    """리밸런싱 유틸리티"""

    @staticmethod
    def is_rebalance_date(current_date: datetime, prev_date: datetime, frequency: str, start_date: datetime = None) -> bool:
        """
        현재 날짜가 리밸런싱 날짜인지 확인 (주 단위)

        Args:
            current_date: 현재 날짜
            prev_date: 이전 날짜
            frequency: 리밸런싱 주기 (weekly_1, weekly_2, weekly_4, weekly_8, weekly_12, weekly_24, weekly_48, none)
            start_date: 시작 날짜 (주 단위 계산용)

        Returns:
            리밸런싱 실행 여부
        """
        if frequency == 'none':
            return False

        # 첫 날은 리밸런싱하지 않음 (초기 매수이므로)
        if prev_date is None:
            return False

        # 주 단위 리밸런싱
        from ..schemas.schemas import DCA_FREQUENCY_MAP
        interval_weeks = DCA_FREQUENCY_MAP.get(frequency)

        if interval_weeks is None:
            # 알 수 없는 주기면 리밸런싱 안 함
            logger.warning(f"알 수 없는 리밸런싱 주기: {frequency}")
            return False

        # start_date가 없으면 prev_date를 기준으로 사용
        ref_date = start_date if start_date else prev_date

        # 시작일로부터 경과한 주 수 계산
        current_weeks = (current_date - ref_date).days // 7
        prev_weeks = (prev_date - ref_date).days // 7

        # 리밸런싱 주기(interval_weeks)마다 실행
        # 예: interval_weeks=4이면 0, 4, 8, 12주차에 리밸런싱
        current_period = current_weeks // interval_weeks
        prev_period = prev_weeks // interval_weeks

        # 새로운 리밸런싱 주기에 진입했으면 True
        return current_period > prev_period

    @staticmethod
    def calculate_target_weights(amounts: Dict[str, float], dca_info: Dict[str, Dict]) -> Dict[str, float]:
        """
        목표 비중 계산 (현금 포함)

        Args:
            amounts: 각 종목의 투자 금액
            dca_info: DCA 정보

        Returns:
            각 종목의 목표 비중 (합이 1.0)
        """
        # 전체 투자금 계산 (현금 포함)
        total_amount = sum(amounts.values())

        if total_amount == 0:
            return {}

        # 목표 비중 계산 (현금 포함)
        target_weights = {
            k: v / total_amount
            for k, v in amounts.items()
        }

        return target_weights

class PortfolioService:
    """포트폴리오 백테스트 서비스"""
    def __init__(self):
        """포트폴리오 서비스 초기화"""
        logger.info("포트폴리오 서비스가 초기화되었습니다")

    @staticmethod
    def calculate_dca_portfolio_returns(
        portfolio_data: Dict[str, pd.DataFrame],
        amounts: Dict[str, float],
        dca_info: Dict[str, Dict],
        start_date: str,
        end_date: str,
        rebalance_frequency: str = "monthly",
        commission: float = 0.0
    ) -> pd.DataFrame:
        """
        분할 매수(DCA)와 리밸런싱을 고려한 포트폴리오 수익률을 계산합니다.

        Args:
            portfolio_data: 각 종목의 가격 데이터 {symbol: DataFrame}
            amounts: 각 종목의 총 투자 금액 {symbol: amount}
            dca_info: 분할 매수 정보 {symbol: {investment_type, dca_periods, monthly_amount}}
            start_date: 시작 날짜
            end_date: 종료 날짜
            rebalance_frequency: 리밸런싱 주기 (monthly, quarterly, annually, none)
            commission: 거래 수수료율 (예: 0.002 = 0.2%)

        Returns:
            포트폴리오 가치와 수익률이 포함된 DataFrame
        """
        # 현금 처리
        cash_amount = 0
        for unique_key, amount in amounts.items():
            if dca_info[unique_key].get('asset_type') == 'cash':
                cash_amount += amount

        stock_amounts = {k: v for k, v in amounts.items() if dca_info[k].get('asset_type') != 'cash'}

        # 날짜 범위 설정
        all_dates = set()
        for unique_key, df in portfolio_data.items():
            if dca_info.get(unique_key, {}).get('asset_type') != 'cash':
                all_dates.update(df.index)

        if not all_dates and cash_amount == 0:
            raise ValueError("유효한 데이터가 없습니다.")

        if not all_dates and cash_amount > 0:
            today = datetime.now().date()
            date_range = pd.DatetimeIndex([today])
        else:
            date_range = pd.DatetimeIndex(sorted(all_dates))

        total_amount = sum(amounts.values())
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

        # 각 종목의 currency 정보 먼저 가져오기
        ticker_currencies = {}
        for unique_key in stock_amounts.keys():
            symbol = dca_info[unique_key]['symbol']
            try:
                ticker_info = get_ticker_info_from_db(symbol)
                ticker_currencies[unique_key] = ticker_info.get('currency', 'USD')
                logger.debug(f"{symbol} currency: {ticker_currencies[unique_key]}")
            except Exception as e:
                logger.warning(f"{symbol} currency 정보 조회 실패: {e}, USD로 가정")
                ticker_currencies[unique_key] = 'USD'

        # 필요한 통화 파악 및 환율 데이터 로드
        required_currencies = set(ticker_currencies.values()) - {'USD'}
        exchange_rates_by_currency = {}  # {currency: {date: rate}}

        # 환율 데이터는 백테스트 시작일보다 충분히 이전부터 로드
        # (백테스트 초반에 누락된 환율을 forward-fill로 채우기 위해)
        exchange_start_date_obj = start_date_obj - timedelta(days=EXCHANGE_RATE_LOOKBACK_DAYS * 2)
        exchange_start_date = exchange_start_date_obj.strftime('%Y-%m-%d')

        for currency in required_currencies:
            if currency not in SUPPORTED_CURRENCIES:
                logger.warning(f"지원하지 않는 통화: {currency}, USD로 처리")
                continue

            exchange_ticker = SUPPORTED_CURRENCIES[currency]
            if exchange_ticker:
                try:
                    # 백테스트 시작일보다 60일 전부터 로드
                    exchange_data = load_ticker_data(exchange_ticker, exchange_start_date, end_date)
                    if exchange_data is not None and not exchange_data.empty:
                        # 백테스트 날짜 범위로 reindex하고 forward-fill 적용
                        # 이렇게 하면 환율 시장 휴일(주말, 공휴일)에도 이전 거래일의 환율이 채워짐
                        exchange_data = exchange_data.reindex(date_range, method='ffill')

                        # 여전히 NaN이 있으면 backward-fill로 채움 (초기 날짜 대비)
                        exchange_data = exchange_data.bfill()

                        currency_rates = {}
                        for date_idx, row in exchange_data.iterrows():
                            if pd.notna(row['Close']):
                                currency_rates[date_idx.date()] = row['Close']

                        exchange_rates_by_currency[currency] = currency_rates
                        logger.info(f"{currency} 환율 데이터 로드 및 전처리 완료: {len(currency_rates)}일치 (reindex + ffill/bfill)")
                except Exception as e:
                    logger.warning(f"{currency} 환율 데이터 로드 실패: {e}")
                    exchange_rates_by_currency[currency] = {}

        # 목표 비중 계산 (리밸런싱용)
        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        # 각 종목의 주식 수 추적
        shares = {key: 0.0 for key in stock_amounts.keys()}

        # 시뮬레이션 변수
        portfolio_values = []
        daily_returns = []
        prev_portfolio_value = 0
        prev_date = None
        is_first_day = True
        available_cash = cash_amount  # 사용 가능한 현금 (총합)
        # 각 현금 항목을 개별 추적
        cash_holdings = {k: v for k, v in amounts.items() if dca_info[k].get('asset_type') == 'cash'}
        total_trades = 0  # 총 거래 횟수 추적
        rebalance_history = []  # 리밸런싱 히스토리
        weight_history = []  # 포트폴리오 비중 변화 이력

        for current_date in date_range:
            daily_cash_inflow = 0.0  # 당일 추가 투자금 (DCA)
            if current_date.date() < start_date_obj.date():
                continue
            if current_date.date() > end_date_obj.date():
                break

            # 현재 가격 가져오기 (필요 시 USD로 변환)
            current_prices = {}
            # 통화별 가장 최근 유효한 환율 캐싱
            last_valid_exchange_rates = {}

            for unique_key in stock_amounts.keys():
                symbol = dca_info[unique_key]['symbol']
                if symbol in portfolio_data:
                    df = portfolio_data[symbol]
                    price_data = df[df.index.date <= current_date.date()]
                    if not price_data.empty:
                        raw_price = price_data['Close'].iloc[-1]

                        # Currency 변환 (원래 통화 -> USD)
                        currency = ticker_currencies.get(unique_key, 'USD')

                        if currency == 'USD':
                            # 이미 USD, 변환 불필요
                            current_prices[unique_key] = raw_price
                        elif currency in exchange_rates_by_currency:
                            # 환율 데이터가 있는 통화 (이미 forward-fill 처리됨)
                            currency_rates = exchange_rates_by_currency[currency]

                            # 해당 날짜의 환율 찾기 (forward-fill로 이미 채워짐)
                            exchange_rate = currency_rates.get(current_date.date())

                            # 여전히 없으면 캐시된 마지막 환율 사용 (fallback)
                            if not exchange_rate or exchange_rate <= 0:
                                if currency in last_valid_exchange_rates:
                                    exchange_rate = last_valid_exchange_rates[currency]
                                    logger.warning(f"{currency} {current_date.date()} 환율 없음, 캐시된 환율 사용: {exchange_rate:.2f}")
                                else:
                                    logger.error(f"{currency} {current_date.date()} 환율 데이터 없음, 해당 종목 건너뛰기")
                                    continue  # 이 종목은 건너뛰기

                            if exchange_rate and exchange_rate > 0:
                                # EUR, GBP, AUD 등: 이미 USD 환율 (EURUSD=X)
                                # KRW, JPY 등: 역수 계산 필요 (1 USD = X KRW)
                                if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
                                    # XXXUSD=X 형태: 1 XXX = Y USD
                                    converted_price = raw_price * exchange_rate
                                else:
                                    # XXX=X 형태: 1 USD = Y XXX
                                    converted_price = raw_price / exchange_rate

                                logger.debug(f"{symbol} 가격 변환: {currency} {raw_price:.2f} -> ${converted_price:.2f} (환율: {exchange_rate:.2f})")
                                current_prices[unique_key] = converted_price
                                last_valid_exchange_rates[currency] = exchange_rate  # 유효한 환율 저장
                        else:
                            # 지원하지 않는 통화, USD로 가정
                            logger.warning(f"{symbol} 지원하지 않는 통화 {currency}, 변환 없이 사용")
                            current_prices[unique_key] = raw_price

            # 첫 날: 초기 매수 (일시불) 또는 DCA 시작
            if is_first_day:
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
                        total_trades += 1  # 초기 매수 거래
                        daily_cash_inflow += amount  # 일시불도 첫 날 유입
                        logger.info(f"{current_date.date()}: {unique_key} 일시불 첫 투자 (금액: ${amount:,.2f}, 가격: ${price:.2f})")
                    else:  # DCA
                        # DCA 첫 달 투자
                        monthly_amount = info['monthly_amount']
                        invest_amount = monthly_amount * (1 - commission)
                        shares[unique_key] = invest_amount / price
                        total_trades += 1  # 첫 DCA 매수 거래
                        daily_cash_inflow += monthly_amount  # DCA 첫 투자 유입
                        logger.info(f"{current_date.date()}: {unique_key} DCA 첫 투자 (금액: ${monthly_amount:,.2f}, interval_weeks: {info.get('interval_weeks', '?')})")

                is_first_day = False
                prev_date = current_date

            # DCA 추가 매수 (주기적 투자)
            if prev_date is not None:
                for symbol, amount in stock_amounts.items():  # symbol로 변수명 통일
                    if symbol not in dca_info:
                        logger.error(f"DCA 정보 없음: {symbol}")
                        continue

                    info = dca_info[symbol]
                    if info['investment_type'] != 'dca':
                        continue

                    # 시작일로부터 경과한 주 수 계산
                    weeks_passed = (current_date - start_date_obj).days // 7
                    prev_weeks_passed = (prev_date - start_date_obj).days // 7

                    # 주 간격이 바뀌었는지 확인 (예: 0주차 → 4주차)
                    interval_weeks = info.get('interval_weeks')
                    if interval_weeks is None:
                        logger.error(f"{symbol}: interval_weeks가 dca_info에 없습니다! dca_info 내용: {info}")
                        logger.error(f"기본값 4 대신 DCA_FREQUENCY_MAP에서 다시 조회 시도: {info.get('dca_frequency')}")
                        from ..schemas.schemas import DCA_FREQUENCY_MAP
                        interval_weeks = DCA_FREQUENCY_MAP.get(info.get('dca_frequency', 'weekly_4'), 4)

                    # 현재 주차가 투자 주기의 배수이고, 이전 날짜와 다른 주기에 속하는지 확인
                    current_period = weeks_passed // interval_weeks
                    prev_period = prev_weeks_passed // interval_weeks

                    # 디버깅: 주기 변화 로깅
                    if current_period != prev_period:
                        logger.info(f"{current_date.date()}: {symbol} 주기 변화 감지 - prev_period={prev_period}, current_period={current_period}, dca_periods={info['dca_periods']}, interval_weeks={interval_weeks}")

                    # 새로운 투자 주기에 진입했고, 아직 투자 횟수를 초과하지 않았으면 투자
                    if current_period > prev_period and current_period < info['dca_periods']:
                        if symbol in current_prices:
                            price = current_prices[symbol]
                            period_amount = info['monthly_amount']  # 회당 투자 금액
                            invest_amount = period_amount * (1 - commission)
                            shares[symbol] += invest_amount / price
                            total_trades += 1  # DCA 추가 매수 거래
                            daily_cash_inflow += period_amount  # DCA 추가 투자 유입 기록
                            logger.info(f"{current_date.date()}: {symbol} DCA 추가 매수 실행! (주기 {current_period + 1}/{info['dca_periods']}, 금액: ${period_amount:,.2f})")
                        else:
                            logger.warning(f"{current_date.date()}: {symbol} DCA 매수 시점이지만 가격 데이터 없음 (주기 {current_period + 1}/{info['dca_periods']})")

            # 리밸런싱 실행
            should_rebalance = RebalanceHelper.is_rebalance_date(
                current_date, prev_date, rebalance_frequency, start_date_obj
            )

            if should_rebalance and len(target_weights) > 1:  # 자산이 2개 이상일 때만
                # 현재 포트폴리오 총 가치 계산 (주식 + 현금)
                total_stock_value = sum(
                    shares[key] * current_prices.get(key, 0)
                    for key in shares.keys()
                    if key in current_prices
                )
                total_portfolio_value = total_stock_value + available_cash

                if total_portfolio_value > 0:
                    # 리밸런싱 전 비중 계산 (현금 포함)
                    weights_before = {}
                    for unique_key in shares.keys():
                        if unique_key in current_prices:
                            current_value = shares[unique_key] * current_prices[unique_key]
                            weights_before[dca_info[unique_key]['symbol']] = current_value / total_portfolio_value
                    # 현금 비중 추가
                    for unique_key in cash_holdings.keys():
                        weights_before[dca_info[unique_key]['symbol']] = cash_holdings[unique_key] / total_portfolio_value

                    # 목표 비중대로 재조정
                    new_shares = {}
                    new_cash_holdings = {}
                    total_commission_cost = 0
                    trades_in_rebalance = 0
                    rebalance_trades = []  # 이번 리밸런싱의 거래 내역

                    for unique_key, target_weight in target_weights.items():
                        target_value = total_portfolio_value * target_weight

                        # 현금 처리
                        if dca_info[unique_key].get('asset_type') == 'cash':
                            current_value = cash_holdings.get(unique_key, 0)
                            # 현금은 거래 수수료 없이 조정
                            new_cash_holdings[unique_key] = target_value

                            # 현금 조정 내역 기록 (차이가 있을 때만)
                            if abs(target_value - current_value) / total_portfolio_value > 0.0001:
                                trades_in_rebalance += 1
                                symbol = dca_info[unique_key]['symbol']
                                if target_value > current_value:
                                    rebalance_trades.append({
                                        'symbol': symbol,
                                        'action': 'increase',  # 현금 증가 (주식 매도)
                                        'amount': abs(target_value - current_value),
                                        'price': 1.0
                                    })
                                else:
                                    rebalance_trades.append({
                                        'symbol': symbol,
                                        'action': 'decrease',  # 현금 감소 (주식 매수)
                                        'amount': abs(target_value - current_value),
                                        'price': 1.0
                                    })

                        # 주식 처리
                        else:
                            if unique_key not in current_prices:
                                new_shares[unique_key] = shares[unique_key]
                                continue

                            price = current_prices[unique_key]
                            current_value = shares[unique_key] * price
                            symbol = dca_info[unique_key]['symbol']

                            # 매도/매수가 발생했는지 확인 (0.01% 이상 차이나면 거래로 간주)
                            if abs(target_value - current_value) / total_portfolio_value > 0.0001:
                                trades_in_rebalance += 1

                                # 거래 내역 기록
                                shares_diff = (target_value / price) - shares[unique_key]
                                if shares_diff > 0:
                                    rebalance_trades.append({
                                        'symbol': symbol,
                                        'action': 'buy',
                                        'shares': abs(shares_diff),
                                        'price': price
                                    })
                                else:
                                    rebalance_trades.append({
                                        'symbol': symbol,
                                        'action': 'sell',
                                        'shares': abs(shares_diff),
                                        'price': price
                                    })

                            # 매도/매수 금액
                            trade_value = abs(target_value - current_value)
                            commission_cost = trade_value * commission
                            total_commission_cost += commission_cost

                            # 새로운 주식 수 계산
                            new_shares[unique_key] = target_value / price

                    # 수수료만큼 전체적으로 비례 축소
                    if total_portfolio_value > total_commission_cost:
                        scale_factor = (total_portfolio_value - total_commission_cost) / total_portfolio_value
                        shares = {k: v * scale_factor for k, v in new_shares.items()}
                        cash_holdings = {k: v * scale_factor for k, v in new_cash_holdings.items()}
                        available_cash = sum(cash_holdings.values())
                    else:
                        shares = new_shares
                        cash_holdings = new_cash_holdings
                        available_cash = sum(cash_holdings.values())

                    # 리밸런싱 후 비중 계산 (현금 포함)
                    weights_after = {}
                    new_total_stock_value = sum(
                        shares[key] * current_prices[key]
                        for key in shares.keys()
                        if key in current_prices
                    )
                    new_total_portfolio_value = new_total_stock_value + available_cash

                    for unique_key in shares.keys():
                        if unique_key in current_prices:
                            new_value = shares[unique_key] * current_prices[unique_key]
                            weights_after[dca_info[unique_key]['symbol']] = new_value / new_total_portfolio_value
                    # 현금 비중 추가
                    for unique_key in cash_holdings.keys():
                        weights_after[dca_info[unique_key]['symbol']] = cash_holdings[unique_key] / new_total_portfolio_value

                    # 리밸런싱 히스토리에 추가
                    if rebalance_trades:  # 실제 거래가 발생한 경우만
                        rebalance_history.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'trades': rebalance_trades,
                            'weights_before': weights_before,
                            'weights_after': weights_after,
                            'commission_cost': total_commission_cost
                        })

                    total_trades += trades_in_rebalance  # 리밸런싱 거래 추가

            # 포트폴리오 가치 계산
            current_portfolio_value = available_cash
            for unique_key in shares.keys():
                if unique_key in current_prices:
                    current_portfolio_value += shares[unique_key] * current_prices[unique_key]

            # 현재 포트폴리오 비중 기록
            current_weights = {'date': current_date.strftime('%Y-%m-%d')}
            if current_portfolio_value > 0:
                # 주식 비중 계산 (symbol을 키로 사용 - 프론트엔드 호환)
                for unique_key in shares.keys():
                    if unique_key in current_prices:
                        stock_value = shares[unique_key] * current_prices[unique_key]
                        symbol = dca_info[unique_key]['symbol']
                        # 같은 symbol이 여러 개 있으면 합산
                        current_weights[symbol] = current_weights.get(symbol, 0) + stock_value / current_portfolio_value
                # 현금 비중 계산 (각 현금 항목 개별 처리)
                for unique_key, amount in cash_holdings.items():
                    symbol = dca_info[unique_key]['symbol']
                    current_weights[symbol] = current_weights.get(symbol, 0) + amount / current_portfolio_value
            weight_history.append(current_weights)

            # 수익률 계산 (추가 투자금 제외)
            if prev_portfolio_value > 0:
                # 순수 수익 = 현재 가치 - 이전 가치 - 당일 추가 투자금
                net_change = current_portfolio_value - prev_portfolio_value - daily_cash_inflow
                daily_return = net_change / prev_portfolio_value
            else:
                daily_return = 0.0

            portfolio_values.append(current_portfolio_value / total_amount)
            daily_returns.append(daily_return)

            prev_portfolio_value = current_portfolio_value
            prev_date = current_date

        # 결과 DataFrame 생성
        valid_dates = [d for d in date_range if start_date_obj.date() <= d.date() <= end_date_obj.date()]

        if len(portfolio_values) != len(valid_dates):
            logger.warning(f"포트폴리오 값 길이 불일치: portfolio_values={len(portfolio_values)}, valid_dates={len(valid_dates)}")
            logger.warning(f"첫 3개 날짜: {valid_dates[:3] if len(valid_dates) > 0 else 'None'}")
            logger.warning(f"마지막 3개 날짜: {valid_dates[-3:] if len(valid_dates) > 0 else 'None'}")
            # 길이가 맞지 않으면 오류 발생 (기본값으로 채우는 대신)
            raise ValueError(f"계산된 포트폴리오 값 개수({len(portfolio_values)})가 날짜 개수({len(valid_dates)})와 일치하지 않습니다.")

        result = pd.DataFrame({
            'Date': valid_dates,
            'Portfolio_Value': portfolio_values,
            'Daily_Return': daily_returns,
            'Cumulative_Return': [(v - 1) * 100 for v in portfolio_values]
        })
        result.set_index('Date', inplace=True)

        # 메타데이터 저장
        result.attrs['total_trades'] = total_trades
        result.attrs['rebalance_history'] = rebalance_history
        result.attrs['weight_history'] = weight_history

        return result
    
    @staticmethod
    def calculate_portfolio_statistics(portfolio_data: pd.DataFrame, total_amount: float) -> Dict[str, Any]:
        start_date = portfolio_data.index[0]
        end_date = portfolio_data.index[-1]
        duration = (end_date - start_date).days

        final_value = portfolio_data['Portfolio_Value'].iloc[-1]
        peak_value = portfolio_data['Portfolio_Value'].max()

        total_return = (final_value - 1) * 100

        # 드로우다운 계산
        running_max = portfolio_data['Portfolio_Value'].expanding().max()
        drawdown = (portfolio_data['Portfolio_Value'] - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0

        # 변동성 및 샤프 비율
        daily_returns = portfolio_data['Daily_Return']
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        annual_return = ((final_value ** (365.25 / duration)) - 1) * 100 if duration > 0 else 0

        # 무위험 수익률을 0으로 가정한 샤프 비율
        sharpe_ratio = (annual_return / annual_volatility) if annual_volatility > 0 else 0

        # 최대 연속 상승/하락일
        daily_changes = daily_returns > 0
        consecutive_gains = PortfolioService._get_max_consecutive(daily_changes, True)
        consecutive_losses = PortfolioService._get_max_consecutive(daily_changes, False)

        # Profit Factor 계산 (이익일 수익률의 합 / 손실일 손실률의 절댓값 합)
        positive_returns = daily_returns[daily_returns > 0]
        negative_returns = daily_returns[daily_returns < 0]

        gross_profit = positive_returns.sum() if len(positive_returns) > 0 else 0
        gross_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (2.0 if gross_profit > 0 else 1.0)

        # 실제 거래 횟수 추출 (DataFrame 메타데이터에서)
        total_trades = portfolio_data.attrs.get('total_trades', 0)

        return {
            'Start': start_date.strftime('%Y-%m-%d'),
            'End': end_date.strftime('%Y-%m-%d'),
            'Duration': f'{duration} days',
            'Initial_Value': total_amount,
            'Final_Value': final_value * total_amount,
            'Peak_Value': peak_value * total_amount,
            'Total_Return': total_return,
            'Annual_Return': annual_return,
            'Annual_Volatility': annual_volatility,
            'Sharpe_Ratio': sharpe_ratio,
            'Max_Drawdown': max_drawdown,
            'Avg_Drawdown': avg_drawdown,
            'Max_Consecutive_Gains': consecutive_gains,
            'Max_Consecutive_Losses': consecutive_losses,
            'Total_Trading_Days': len(portfolio_data),
            'Total_Trades': total_trades,
            'Positive_Days': len(daily_returns[daily_returns > 0]),
            'Negative_Days': len(daily_returns[daily_returns < 0]),
            'Win_Rate': len(daily_returns[daily_returns > 0]) / len(daily_returns) * 100 if len(daily_returns) > 0 else 0,
            'Profit_Factor': profit_factor
        }
    
    @staticmethod
    def _get_max_consecutive(series: pd.Series, target_value: bool) -> int:
        """연속된 값의 최대 길이 계산"""
        max_count = 0
        current_count = 0
        
        for value in series:
            if value == target_value:
                current_count += 1
                max_count = max(max_count, current_count)
            else:
                current_count = 0
        
        return max_count
    
    async def _calculate_realistic_equity_curve(self, request: PortfolioBacktestRequest,
                                              portfolio_results: Dict, total_amount: float) -> Tuple[Dict, Dict, List]:
        """
        개별 종목 백테스트의 실제 equity curve를 합산하여 포트폴리오 equity curve 계산
        (매수/매도 타이밍이 정확히 반영됨)

        Returns:
            Tuple[equity_curve, daily_returns, weight_history]
        """
        from datetime import datetime
        import pandas as pd

        # 각 종목의 equity curve 수집
        equity_curves_by_symbol = {}
        all_dates = set()

        for symbol, result in portfolio_results.items():
            strategy_stats = result.get('strategy_stats', {})
            equity_curve_dict = strategy_stats.get('equity_curve')

            if equity_curve_dict and isinstance(equity_curve_dict, dict):
                equity_curves_by_symbol[symbol] = equity_curve_dict
                all_dates.update(equity_curve_dict.keys())
                logger.info(f"{symbol} equity curve: {len(equity_curve_dict)}일치")
            else:
                # equity curve가 없으면 (예: 현금) 초기값으로 고정
                amount = result.get('amount', 0)
                equity_curves_by_symbol[symbol] = None
                logger.info(f"{symbol}: equity curve 없음, 고정값 ${amount}")

        if not all_dates:
            # equity curve가 하나도 없으면 fallback
            logger.warning("모든 종목의 equity curve가 없음, fallback 사용")
            return self._fallback_equity_curve(request, portfolio_results, total_amount)

        date_range = sorted(all_dates)

        equity_curve = {}
        daily_returns = {}
        weight_history = []
        prev_portfolio_value = total_amount

        for i, date_str in enumerate(date_range):
            portfolio_value = 0
            symbol_equities = {}  # 각 종목의 equity 저장

            # 각 종목의 해당 날짜 equity 합산
            for symbol, result in portfolio_results.items():
                equity_curve_dict = equity_curves_by_symbol.get(symbol)
                symbol_equity = 0

                if equity_curve_dict:
                    # 전략 실행 결과의 equity curve 사용
                    if date_str in equity_curve_dict:
                        symbol_equity = equity_curve_dict[date_str]
                    elif i == 0:
                        # 첫날에 데이터가 없으면 초기 투자금
                        symbol_equity = result.get('amount', 0)
                    else:
                        # 중간에 데이터가 없으면 마지막 값 사용 (forward fill)
                        symbol_equity = result.get('final_value', result.get('amount', 0))
                else:
                    # equity curve가 없는 종목 (예: 현금)
                    symbol_equity = result.get('amount', 0)

                symbol_equities[symbol] = symbol_equity
                portfolio_value += symbol_equity

            # 일일 수익률 계산
            if i == 0:
                daily_return = 0.0
            else:
                daily_return = (portfolio_value - prev_portfolio_value) / prev_portfolio_value * 100 if prev_portfolio_value > 0 else 0.0

            equity_curve[date_str] = portfolio_value
            daily_returns[date_str] = daily_return

            # 포트폴리오 비중 계산
            current_weights = {'date': date_str}
            if portfolio_value > 0:
                for symbol, symbol_equity in symbol_equities.items():
                    current_weights[symbol] = symbol_equity / portfolio_value
            else:
                for symbol in symbol_equities.keys():
                    current_weights[symbol] = 0

            weight_history.append(current_weights)
            prev_portfolio_value = portfolio_value

        logger.info(f"포트폴리오 equity curve 및 weight history 계산 완료: {len(equity_curve)}일치")
        return equity_curve, daily_returns, weight_history
    
    def _fallback_equity_curve(self, request: PortfolioBacktestRequest,
                              portfolio_results: Dict, total_amount: float) -> Tuple[Dict, Dict, List]:
        """
        데이터가 없을 때 사용하는 기본 equity curve (선형)

        Returns:
            Tuple[equity_curve, daily_returns, weight_history]
        """
        from datetime import datetime
        import pandas as pd
        
        start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
        date_range = pd.date_range(start=start_date_obj, end=end_date_obj, freq='D')
        
        # 포트폴리오 최종 가치 계산
        final_portfolio_value = sum(result['final_value'] for result in portfolio_results.values())
        growth_rate = (final_portfolio_value / total_amount - 1)
        
        equity_curve = {}
        daily_returns = {}
        weight_history = []
        prev_equity = total_amount

        # 초기 비중 계산 (고정된 비중으로 가정)
        initial_weights = {}
        for symbol, result in portfolio_results.items():
            initial_weights[symbol] = result.get('amount', 0) / total_amount if total_amount > 0 else 0

        for i, date in enumerate(date_range):
            if i == 0:
                daily_return = 0.0
                equity_value = total_amount
            else:
                # 선형 성장 가정
                progress = i / (len(date_range) - 1) if len(date_range) > 1 else 1
                equity_value = total_amount * (1 + growth_rate * progress)
                daily_return = (equity_value - prev_equity) / prev_equity * 100 if prev_equity > 0 else 0.0

            equity_curve[date.strftime('%Y-%m-%d')] = equity_value
            daily_returns[date.strftime('%Y-%m-%d')] = daily_return

            # 비중 기록 (fallback에서는 초기 비중 유지)
            current_weights = {'date': date.strftime('%Y-%m-%d')}
            current_weights.update(initial_weights)
            weight_history.append(current_weights)

            prev_equity = equity_value

        return equity_curve, daily_returns, weight_history
    
    async def run_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        포트폴리오 백테스트 실행
        
        Args:
            request: 포트폴리오 백테스트 요청
            
        Returns:
            백테스트 결과
        """
        try:
            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            logger.info(f"포트폴리오 백테스트 시작: 전략={strategy_name}, 종목수={len(request.portfolio)}")

            # 전략이 buy_hold_strategy가 아닌 경우 개별 종목별로 전략 백테스트 실행
            if strategy_name != "buy_hold_strategy":
                return await self.run_strategy_portfolio_backtest(request)
            else:
                return await self.run_buy_and_hold_portfolio_backtest(request)
                
        except Exception as e:
            logger.exception("포트폴리오 백테스트 실행 중 오류 발생")
            return {
                'status': 'error',
                'error': str(e),
                'code': 'PORTFOLIO_BACKTEST_ERROR'
            }
    
    async def run_strategy_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        전략 기반 포트폴리오 백테스트 실행
        각 종목에 동일한 전략을 적용하고 투자 금액으로 결합
        """
        try:
            portfolio_results = {}
            individual_returns = {}
            total_portfolio_value = 0
            # amount/weight 동시 지원: amount가 없고 weight만 있으면 환산
            if all(item.amount is not None for item in request.portfolio):
                total_amount = sum(item.amount for item in request.portfolio)
                amounts = {item.symbol: item.amount for item in request.portfolio}
            elif all(item.weight is not None for item in request.portfolio):
                # weight만 입력된 경우, 총 투자금액을 100으로 가정하거나, 프론트에서 별도 입력받을 수도 있음
                # 여기서는 100 단위로 환산 (실제 투자금액은 프론트에서 amount로 입력 권장)
                total_amount = 100.0
                amounts = {item.symbol: total_amount * (item.weight / 100.0) for item in request.portfolio}
            else:
                raise ValidationError('포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다.')
            
            strategy_name = request.strategy.value if hasattr(request.strategy, 'value') else str(request.strategy)
            logger.info(f"전략 기반 백테스트: {strategy_name}, 총 투자금액: ${total_amount:,.2f}")
            
            # 각 종목별로 전략 백테스트 실행
            for idx, item in enumerate(request.portfolio):
                symbol = item.symbol
                # amount/weight 동시 지원
                amount = amounts[symbol]
                weight = amount / total_amount if total_amount > 0 else 0.0
                
                # 현금 처리 (수익률 0%, 전략 적용 안함)
                if item.asset_type == 'cash':
                    logger.info(f"현금 자산 {symbol} 처리 (투자금액: ${amount:,.2f}, 비중: {weight:.3f})")
                    
                    portfolio_results[symbol] = {
                        'symbol': symbol,
                        'initial_value': amount,
                        'final_value': amount,  # 현금은 변동 없음
                        'return_pct': 0.0,  # 현금 수익률 0%
                        'weight': weight,
                        'amount': amount,
                        'strategy_stats': {
                            'total_trades': 0,
                            'win_rate_pct': 0.0,
                            'max_drawdown_pct': 0.0,
                            'sharpe_ratio': 0.0,
                            'final_equity': amount
                        }
                    }
                    
                    individual_returns[symbol] = {
                        'symbol': symbol,
                        'weight': weight,
                        'amount': amount,
                        'return': 0.0,
                        'initial_value': amount,
                        'final_value': amount,
                        'trades': 0,
                        'win_rate': 0.0
                    }
                    
                    total_portfolio_value += amount
                    logger.info(f"현금 자산 완료: 0.00% 수익률")
                    continue
                
                logger.info(f"종목 {symbol} (#{idx+1}) 전략 백테스트 실행 (투자금액: ${amount:,.2f}, 비중: {weight:.3f})")
                
                # 개별 종목 백테스트 요청 생성
                strategy_value = strategy_name  # 이미 위에서 변환한 strategy_name 사용
                backtest_req = BacktestRequest(
                    ticker=symbol,
                    start_date=request.start_date,
                    end_date=request.end_date,
                    initial_cash=amount,
                    strategy=strategy_value,
                    strategy_params=request.strategy_params or {}
                )
                
                try:
                    # 개별 종목 백테스트 실행
                    result = await backtest_service.run_backtest(backtest_req)
                    
                    if result and hasattr(result, 'final_equity'):
                        final_value = result.final_equity
                        initial_value = amount
                        stock_return = (final_value / initial_value - 1) * 100
                        
                        portfolio_results[symbol] = {
                            'symbol': symbol,
                            'initial_value': initial_value,
                            'final_value': final_value,
                            'return_pct': stock_return,
                            'weight': weight,
                            'amount': amount,
                            'strategy_stats': result.__dict__  # 객체를 딕셔너리로 변환
                        }
                        
                        individual_returns[symbol] = {
                            'symbol': symbol,
                            'weight': weight,
                            'amount': amount,
                            'return': stock_return,
                            'initial_value': initial_value,
                            'final_value': final_value,
                            'trades': getattr(result, 'total_trades', 0),
                            'win_rate': getattr(result, 'win_rate_pct', 0)
                        }
                        
                        total_portfolio_value += final_value
                        
                        logger.info(f"종목 {symbol} (#{idx+1}) 완료: {stock_return:.2f}% 수익률, 거래수: {getattr(result, 'total_trades', 0)}")
                    else:
                        logger.warning(f"종목 {symbol} 백테스트 실패: 결과가 없거나 final_equity 속성이 없음")
                        
                except Exception as e:
                    logger.error(f"종목 {symbol} 백테스트 오류: {str(e)}")
                    continue
            
            if not portfolio_results:
                raise ValueError("모든 종목의 백테스트가 실패했습니다.")
            
            # 포트폴리오 전체 통계 계산
            portfolio_return = (total_portfolio_value / total_amount - 1) * 100
            total_trades = sum(result.get('strategy_stats', {}).get('total_trades', 0) 
                             for result in portfolio_results.values())
            
            # 가중 평균 승률 계산
            weighted_win_rate = sum(
                result['weight'] * result.get('strategy_stats', {}).get('win_rate_pct', 0)
                for result in portfolio_results.values()
            )
            
            # 가중 평균 최대 드로우다운 계산
            weighted_max_drawdown = sum(
                result['weight'] * abs(result.get('strategy_stats', {}).get('max_drawdown_pct', 0))
                for result in portfolio_results.values()
            )
            
            # 가중 평균 샤프 비율 계산
            weighted_sharpe_ratio = sum(
                result['weight'] * result.get('strategy_stats', {}).get('sharpe_ratio', 0)
                for result in portfolio_results.values()
            )
            
            # 가중 평균 프로핏 팩터 계산
            weighted_profit_factor = sum(
                result['weight'] * result.get('strategy_stats', {}).get('profit_factor', 1.0)
                for result in portfolio_results.values()
            )
            
            # 백테스트 기간 계산
            from datetime import datetime
            import numpy as np
            start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
            duration_days = (end_date_obj - start_date_obj).days

            # 연간 수익률 계산
            annual_return = ((total_portfolio_value / total_amount) ** (365.25 / duration_days) - 1) * 100 if duration_days > 0 else 0

            # 먼저 equity curve, daily returns, weight history 계산
            equity_curve, daily_returns, weight_history = await self._calculate_realistic_equity_curve(
                request, portfolio_results, total_amount
            )

            # daily_returns로부터 연간 변동성 계산
            returns_list = [v for v in daily_returns.values()]
            daily_volatility = np.std(returns_list) if len(returns_list) > 1 else 0.0
            annual_volatility = daily_volatility * np.sqrt(252)  # 연간 거래일 수로 연간화

            # daily_returns로부터 프로핏 팩터 계산
            positive_returns = [r for r in returns_list if r > 0]
            negative_returns = [r for r in returns_list if r < 0]
            total_gains = sum(positive_returns) if positive_returns else 0.0
            total_losses = abs(sum(negative_returns)) if negative_returns else 0.0
            actual_profit_factor = total_gains / total_losses if total_losses > 0 else 0.0

            # Positive/Negative Days 계산
            positive_days = len(positive_returns)
            negative_days = len(negative_returns)

            # 포트폴리오 통계 (프론트엔드 호환)
            portfolio_statistics = {
                'Start': request.start_date,
                'End': request.end_date,
                'Duration': f'{duration_days} days',
                'Initial_Value': total_amount,
                'Final_Value': total_portfolio_value,
                'Peak_Value': total_portfolio_value,  # 전략 기반에서는 최종값과 동일하게 가정
                'Total_Return': portfolio_return,
                'Annual_Return': annual_return,
                'Annual_Volatility': annual_volatility,  # 실제 계산된 연간 변동성
                'Sharpe_Ratio': weighted_sharpe_ratio,
                'Max_Drawdown': -weighted_max_drawdown,  # 음수로 표시
                'Avg_Drawdown': -weighted_max_drawdown / 2,  # 평균 드로우다운 추정
                'Max_Consecutive_Gains': 0,  # 전략 기반에서는 계산 복잡
                'Max_Consecutive_Losses': 0,  # 전략 기반에서는 계산 복잡
                'Total_Trading_Days': duration_days,
                'Total_Trades': total_trades,  # 전체 거래 횟수 추가
                'Positive_Days': positive_days,  # 실제 계산된 값
                'Negative_Days': negative_days,  # 실제 계산된 값
                'Win_Rate': weighted_win_rate,
                'Profit_Factor': actual_profit_factor  # 실제 계산된 프로핏 팩터
            }

            # individual_results를 리스트 형태로 변환 (테스트 호환성)
            individual_results_list = []
            for symbol, returns in individual_returns.items():
                individual_results_list.append({
                    'ticker': returns['symbol'],
                    'final_equity': returns['final_value'],
                    'total_return_pct': returns['return'],
                    'sharpe_ratio': portfolio_results[symbol].get('strategy_stats', {}).get('sharpe_ratio', 0.0),
                    'weight': returns['weight'],
                    'amount': returns['amount'],
                    'trades': returns.get('trades', 0),
                    'win_rate': returns.get('win_rate', 0.0)
                })

            result = {
                'status': 'success',
                'data': {
                    'portfolio_statistics': portfolio_statistics,
                    'individual_returns': individual_returns,
                    'individual_results': individual_results_list,  # 테스트 호환성을 위한 리스트 형태
                    'portfolio_result': {  # 테스트에서 기대하는 구조
                        'total_equity': total_portfolio_value,
                        'total_return_pct': portfolio_return
                    },
                    'portfolio_composition': [
                        {'symbol': result['symbol'], 
                         'weight': result['weight'], 'amount': result['amount']}
                        for symbol, result in portfolio_results.items()
                    ],
                    'strategy_details': {
                        symbol: result['strategy_stats']
                        for symbol, result in portfolio_results.items()
                    },
                    'equity_curve': equity_curve,
                    'daily_returns': daily_returns,
                    'weight_history': weight_history,
                    'rebalance_history': []  # 전략 포트폴리오는 리밸런싱 없음
                }
            }
            
            logger.info(f"전략 포트폴리오 백테스트 완료: 총 수익률 {portfolio_return:.2f}%")
            
            return recursive_serialize(result)
            
        except Exception as e:
            logger.exception("전략 포트폴리오 백테스트 실행 중 오류 발생")
            return {
                'status': 'error',
                'error': str(e),
                'code': 'STRATEGY_PORTFOLIO_BACKTEST_ERROR'
            }
    
    async def run_buy_and_hold_portfolio_backtest(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        Buy & Hold 포트폴리오 백테스트 실행 (투자 금액 기반)
        현금(CASH)과 주식을 함께 처리, 분할 매수(DCA) 지원
        """
        try:
            # 각 종목의 데이터 수집 (중복 종목 지원)
            portfolio_data = {}
            amounts = {}  # 실제 총 투자 금액 (DCA의 경우 회당 금액 × 횟수)

            # DCA 주기 매핑
            from ..schemas.schemas import DCA_FREQUENCY_MAP

            # 백테스트 기간 계산 (주 수)
            from datetime import datetime
            start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')

            # 백테스트 기간을 주 단위로 계산
            backtest_days = (end_date_obj - start_date_obj).days
            backtest_weeks = backtest_days // 7  # 주 단위 (정수 나눗셈)

            logger.info(f"백테스트 기간: {request.start_date} ~ {request.end_date} ({backtest_days}일, {backtest_weeks}주)")

            # 분할 매수 정보 수집 및 총 투자 금액 계산
            dca_info = {}
            cash_amount = 0

            # 먼저 모든 종목의 투자 타입을 확인하고 총 금액 계산
            for item in request.portfolio:
                symbol = item.symbol
                investment_type = getattr(item, 'investment_type', 'lump_sum')
                dca_frequency = getattr(item, 'dca_frequency', 'weekly_4')

                # DCA 투자 횟수 계산: 백테스트 기간(주) / 투자 간격(주) + 1 (0주차 첫 투자 포함)
                interval_weeks = DCA_FREQUENCY_MAP.get(dca_frequency, 4)
                # 예: 52주 / 24주 = 2, 2 + 1 = 3회 (0주, 24주, 48주)
                dca_periods = max(1, (backtest_weeks // interval_weeks) + 1) if investment_type == 'dca' else 1

                asset_type = getattr(item, 'asset_type', 'stock')

                # amount 또는 weight 기반으로 회당 투자 금액 계산
                if item.amount is not None:
                    per_period_amount = item.amount  # 입력한 금액 = 회당 투자 금액
                elif item.weight is not None:
                    # weight 모드는 나중에 처리
                    per_period_amount = 0
                else:
                    raise ValidationError('포트폴리오 내 모든 종목은 amount 또는 weight를 입력해야 합니다.')

                # 총 투자 금액 계산
                if investment_type == 'dca':
                    # 분할 매수: 회당 금액 × 횟수
                    total_investment = per_period_amount * dca_periods
                else:
                    # 일시불: 회당 금액 = 총 금액
                    total_investment = per_period_amount

                amounts[symbol] = total_investment

                # 분할 매수 정보 저장
                dca_info[symbol] = {
                    'symbol': symbol,
                    'investment_type': investment_type,
                    'dca_frequency': dca_frequency,
                    'dca_periods': dca_periods,
                    'interval_weeks': interval_weeks,  # DCA 투자 간격 (주)
                    'monthly_amount': per_period_amount,  # 회당 투자 금액 (legacy 필드명 유지)
                    'asset_type': asset_type
                }

                # 진짜 현금 자산 처리 (asset_type이 'cash'인 경우)
                if asset_type == 'cash':
                    # 현금 처리
                    cash_amount += total_investment
                    logger.info(f"현금 자산 {symbol} 추가 (금액: ${total_investment:,.2f})")
                    continue

                logger.info(f"종목 {symbol} 데이터 로드 중 (총 투자금액: ${total_investment:,.2f}, 방식: {investment_type})")

                if investment_type == 'dca':
                    logger.info(f"분할 매수: {dca_periods}회에 걸쳐 회당 ${per_period_amount:,.2f}씩 (총 ${total_investment:,.2f})")
                    logger.info(f"DCA 설정: frequency={dca_frequency}, interval_weeks={interval_weeks}, dca_periods={dca_periods}")

                # DB에서 데이터 로드
                df = load_ticker_data(symbol, request.start_date, request.end_date)

                if df is None or df.empty:
                    logger.warning(f"종목 {symbol}의 데이터가 없습니다.")
                    continue

                portfolio_data[symbol] = df
                logger.info(f"종목 {symbol} 데이터 로드 완료: {len(df)} 행")

            # 총 투자 금액 계산
            total_amount = sum(amounts.values())
            
            # 현금만 있는 경우 처리
            if not portfolio_data and cash_amount > 0:
                logger.info("현금만 있는 포트폴리오로 백테스트 실행")
                
                # 현금 전용 결과 생성
                from datetime import datetime
                start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
                end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
                duration_days = (end_date_obj - start_date_obj).days
                
                # 현금은 수익률 0%
                statistics = {
                    'Start': request.start_date,
                    'End': request.end_date,
                    'Duration': f'{duration_days} days',
                    'Initial_Value': cash_amount,
                    'Final_Value': cash_amount,
                    'Peak_Value': cash_amount,
                    'Total_Return': 0.0,
                    'Annual_Return': 0.0,
                    'Annual_Volatility': 0.0,
                    'Sharpe_Ratio': 0.0,
                    'Max_Drawdown': 0.0,
                    'Avg_Drawdown': 0.0,
                    'Max_Consecutive_Gains': 0,
                    'Max_Consecutive_Losses': 0,
                    'Total_Trading_Days': duration_days,
                    'Positive_Days': 0,
                    'Negative_Days': 0,
                    'Win_Rate': 0.0
                }
                
                individual_returns = {
                    'CASH': {
                        'weight': 1.0,
                        'amount': cash_amount,
                        'return': 0.0,
                        'start_price': 1.0,
                        'end_price': 1.0,
                        'investment_type': 'lump_sum',
                        'asset_type': 'cash'  # 진짜 현금 자산임을 표시
                    }
                }
                
                # 기본 equity curve (현금은 변동 없음)
                date_range = pd.date_range(start=start_date_obj, end=end_date_obj, freq='D')
                equity_curve = {
                    date.strftime('%Y-%m-%d'): cash_amount
                    for date in date_range
                }
                daily_returns = {
                    date.strftime('%Y-%m-%d'): 0.0
                    for date in date_range
                }
                
                result = {
                    'status': 'success',
                    'data': {
                        'portfolio_statistics': statistics,
                        'individual_returns': individual_returns,
                        'portfolio_composition': [
                            {'symbol': 'CASH', 'weight': 1.0, 'amount': cash_amount, 'investment_type': 'lump_sum'}
                        ],
                        'equity_curve': equity_curve,
                        'daily_returns': daily_returns
                    }
                }
                
                return recursive_serialize(result)
            
            # 주식과 현금이 모두 없는 경우
            if not portfolio_data and cash_amount == 0:
                raise ValueError("포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다.")
            
            # 분할 매수를 고려한 포트폴리오 수익률 계산
            logger.info("분할 매수 및 리밸런싱을 고려한 포트폴리오 수익률 계산 중...")
            portfolio_result = self.calculate_dca_portfolio_returns(
                portfolio_data, amounts, dca_info, request.start_date, request.end_date,
                request.rebalance_frequency, request.commission
            )
            
            # 통계 계산
            logger.info("포트폴리오 통계 계산 중...")
            statistics = self.calculate_portfolio_statistics(portfolio_result, total_amount)
            
            # 개별 종목 수익률 (참고용, 현금 포함)
            individual_returns = {}
            strategy_details = {}  # 거래 로그를 저장할 딕셔너리

                # 현금 수익률 추가
            if cash_amount > 0:
                individual_returns['CASH'] = {
                    'weight': cash_amount / total_amount,
                    'amount': cash_amount,
                    'return': 0.0,  # 현금 수익률은 0%
                    'start_price': 1.0,
                    'end_price': 1.0,
                    'investment_type': 'lump_sum',
                    'asset_type': 'cash'  # 진짜 현금 자산임을 표시
                }
            
            # 주식 수익률 추가 (중복 종목 지원)
            for unique_key, amount in amounts.items():
                if unique_key.endswith('_CASH') or dca_info[unique_key].get('asset_type') == 'cash':
                    continue
                    
                symbol = dca_info[unique_key]['symbol']
                
                if symbol in portfolio_data:
                    df = portfolio_data[symbol]
                    if len(df) > 0:
                        investment_type = dca_info[unique_key]['investment_type']
                        weight = amount / total_amount
                        
                        if investment_type == 'lump_sum':
                            # 일시불: 시작가 대비 종료가로 수익률 계산
                            start_price = df['Close'].iloc[0]
                            end_price = df['Close'].iloc[-1]
                            individual_return = (end_price / start_price - 1) * 100

                            # 일시불 매수 거래 로그 생성
                            start_date = df.index[0]
                            total_shares = amount / start_price
                            lump_sum_trade_log = [{
                                'EntryTime': start_date.isoformat(),
                                'EntryPrice': float(start_price),
                                'Size': float(total_shares),
                                'ExitTime': None,
                                'ExitPrice': None,
                                'PnL': None,
                                'ReturnPct': None,
                                'Duration': None,
                            }]

                            individual_returns[unique_key] = {
                                'symbol': symbol,
                                'weight': weight,
                                'amount': amount,
                                'return': individual_return,
                                'start_price': start_price,
                                'end_price': end_price,
                                'investment_type': investment_type,
                                'dca_periods': None
                            }

                            # strategy_details에 거래 로그 저장
                            strategy_details[unique_key] = {
                                'trade_log': lump_sum_trade_log
                            }
                            
                        else:  # DCA
                            # 분할매수: DCACalculator를 사용하여 수익률 계산
                            dca_periods = dca_info[unique_key]['dca_periods']
                            monthly_amount = dca_info[unique_key]['monthly_amount']

                            total_shares, average_price, individual_return, dca_trade_log = DCACalculator.calculate_dca_shares_and_return(
                                df, monthly_amount, dca_periods, request.start_date
                            )

                            end_price = df['Close'].iloc[-1]

                            individual_returns[unique_key] = {
                                'symbol': symbol,
                                'weight': weight,
                                'amount': amount,
                                'return': individual_return,
                                'start_price': average_price,  # DCA의 경우 평균 매수 단가
                                'end_price': end_price,
                                'investment_type': investment_type,
                                'dca_periods': dca_periods
                            }

                            # strategy_details에 거래 로그 저장
                            strategy_details[unique_key] = {
                                'trade_log': dca_trade_log
                            }
            
            # individual_results를 리스트 형태로 변환 (테스트 호환성)
            individual_results_list = []
            for unique_key, returns in individual_returns.items():
                individual_results_list.append({
                    'ticker': returns['symbol'] if returns.get('symbol') else unique_key,
                    'final_equity': returns['amount'] + (returns['amount'] * returns['return'] / 100),
                    'total_return_pct': returns['return'],
                    'sharpe_ratio': 0.0,  # Buy & Hold에서는 계산하지 않음
                    'weight': returns['weight'],
                    'amount': returns['amount'],
                    'trades': 1 if returns.get('symbol', '') != 'CASH' else 0,
                    'win_rate': 100.0 if returns['return'] > 0 else 0.0
                })

            # 리밸런싱 히스토리와 비중 변화 데이터 추출
            rebalance_history = portfolio_result.attrs.get('rebalance_history', [])
            weight_history = portfolio_result.attrs.get('weight_history', [])

            # 결과 포맷팅
            result = {
                'status': 'success',
                'data': {
                    'portfolio_statistics': statistics,
                    'individual_returns': individual_returns,
                    'individual_results': individual_results_list,  # 테스트 호환성을 위한 리스트 형태
                    'portfolio_result': {  # 테스트에서 기대하는 구조
                        'total_equity': statistics['Final_Value'],
                        'total_return_pct': statistics['Total_Return']
                    },
                    'portfolio_composition': [
                        {
                            'symbol': dca_info[unique_key]['symbol'],  # 실제 symbol 사용 (프론트엔드 호환)
                            'weight': amount / total_amount,
                            'amount': amount,
                            'investment_type': dca_info[unique_key]['investment_type'],
                            'dca_periods': dca_info[unique_key]['dca_periods'] if dca_info[unique_key]['investment_type'] == 'dca' else None,
                            'asset_type': dca_info[unique_key].get('asset_type', 'stock')
                        }
                        for unique_key, amount in amounts.items()
                    ],
                    'equity_curve': {
                        date.strftime('%Y-%m-%d'): value * total_amount
                        for date, value in portfolio_result['Portfolio_Value'].items()
                    },
                    # ============================================================
                    # 수익률 표현 형식: 백분율(Percentage) vs 소수(Decimal)
                    # ============================================================
                    #
                    # **API 응답 형식: 백분율 (2.5 = 2.5%)**
                    # - 사용자에게 표시되는 모든 수익률은 백분율로 반환
                    # - 예: 0.025 (decimal) → 2.5 (percentage)
                    # - 이유: UI 표시, 툴팁, 차트 레이블 등 90%의 사용 사례가 백분율 표시
                    # - API 응답의 가독성 향상 ({"daily_return": 2.5} vs {"daily_return": 0.025})
                    #
                    # **계산에서의 형식: 소수 (0.025 = 2.5%)**
                    # - 내부 계산(복리 수익률, 누적 수익률 등)은 소수 형식 사용
                    # - 예: 복리 계산 시 1.025 = 1 + 0.025 (2.5% 수익)
                    # - 프론트엔드에서 계산 필요 시 `/100`으로 소수로 변환
                    #
                    # **변환 흐름:**
                    # 1. 백엔드 계산: 0.025 (소수)
                    # 2. API 응답: 2.5 (백분율, `return_val * 100`)  ← 여기서 한 번만 변환
                    # 3. 프론트 표시: "2.5%" (그대로 사용)
                    # 4. 프론트 계산: 2.5 / 100 = 0.025 (필요 시 역변환)
                    #
                    # **주의사항:**
                    # - 이중 변환 방지: API에서 이미 백분율로 반환했으므로 추가 변환 불필요
                    # - 계산 필요 시에만 `/100` 사용 (예: BenchmarkIndexChart의 복리 계산)
                    # ============================================================
                    'daily_returns': {
                        date.strftime('%Y-%m-%d'): return_val * 100  # 소수 → 백분율 변환 (0.025 → 2.5)
                        for date, return_val in portfolio_result['Daily_Return'].items()
                    },
                    'strategy_details': strategy_details,  # 거래 로그 포함
                    'rebalance_history': rebalance_history,
                    'weight_history': weight_history
                }
            }
            
            logger.info(f"Buy & Hold 포트폴리오 백테스트 완료: 총 수익률 {statistics['Total_Return']:.2f}%")
            
            return recursive_serialize(result)
            
        except Exception as e:
            logger.exception("Buy & Hold 포트폴리오 백테스트 실행 중 오류 발생")
            return {
                'status': 'error',
                'error': str(e),
                'code': 'BUY_HOLD_PORTFOLIO_BACKTEST_ERROR'
            }


# 전역 인스턴스 생성 (기존 패턴 유지)
portfolio_service = PortfolioService()
