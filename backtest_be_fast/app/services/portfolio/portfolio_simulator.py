"""
포트폴리오 시뮬레이션 실행

**역할**:
- 포트폴리오 시뮬레이션 루프 실행
- 포트폴리오 상태 관리 및 추적
- 가격 데이터 처리 및 환율 변환
- 상장폐지 종목 감지

**의존성**:
- app/services/portfolio/portfolio_dca_manager.py: DCA 관리
- app/services/portfolio/portfolio_rebalancer.py: 리밸런싱
- app/services/rebalance_helper.py: 리밸런싱 헬퍼
- app/utils/currency_converter.py: 통화 변환
- app/constants/data_loading.py: 데이터 로딩 상수
"""

import asyncio
import logging
from typing import Dict, Any, Tuple
from datetime import datetime, date
import pandas as pd
import numpy as np

from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.rebalance_helper import RebalanceHelper, get_next_nth_weekday, get_weekday_occurrence
from app.utils.currency_converter import currency_converter
from app.constants.data_loading import TradingThresholds

logger = logging.getLogger(__name__)


class PortfolioSimulator:
    """포트폴리오 시뮬레이션 클래스"""

    def __init__(
        self,
        dca_manager: PortfolioDcaManager = None,
        rebalancer: PortfolioRebalancer = None
    ):
        """
        포트폴리오 시뮬레이터 초기화

        Args:
            dca_manager: DCA 관리 매니저
            rebalancer: 리밸런싱 리밸런서
        """
        self.dca_manager = dca_manager or PortfolioDcaManager()
        self.rebalancer = rebalancer or PortfolioRebalancer()
        self.logger = logging.getLogger(__name__)

    def initialize_portfolio_state(
        self,
        stock_amounts: Dict[str, float],
        cash_amount: float,
        amounts: Dict[str, float],
        dca_info: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """
        포트폴리오 시뮬레이션을 위한 모든 추적 변수를 초기화합니다.

        Args:
            stock_amounts: 주식 종목별 투자 금액
            cash_amount: 총 현금 금액
            amounts: 전체 자산 금액 (주식 + 현금)
            dca_info: 분할 매수 정보

        Returns:
            초기화된 상태 딕셔너리
        """
        return {
            'shares': {key: 0.0 for key in stock_amounts.keys()},
            'portfolio_values': [],
            'daily_returns': [],
            'prev_portfolio_value': 0,
            'prev_date': None,
            'is_first_day': True,
            'available_cash': cash_amount,
            'cash_holdings': {k: v for k, v in amounts.items() if dca_info[k].get('asset_type') == 'cash'},
            'total_trades': 0,
            'rebalance_history': [],
            'weight_history': [],
            'last_rebalance_date': None,
            'original_rebalance_nth': None,
            'last_valid_prices': {},
            'last_price_date': {},
            'delisted_stocks': set()
        }

    def detect_and_update_delisting(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, Dict],
        delisted_stocks: set,
        last_valid_prices: Dict[str, float],
        last_price_date: Dict[str, date]
    ) -> None:
        """
        상장폐지 종목을 감지하고 상태를 업데이트합니다.

        **역할**:
        - 30일 이상 가격 데이터가 없는 종목을 상장폐지로 판단
        - 마지막 유효 가격과 날짜를 추적
        - 재상장 케이스 처리

        Args:
            current_date: 현재 시뮬레이션 날짜
            stock_amounts: 종목별 투자 금액
            current_prices: 종목별 현재 가격 (MODIFIED)
            dca_info: 종목 정보
            delisted_stocks: 상장폐지 종목 집합 (MODIFIED)
            last_valid_prices: 마지막 유효 가격 (MODIFIED)
            last_price_date: 마지막 가격 날짜 (MODIFIED)
        """
        # 상장폐지 감지: 가격 데이터가 30일 이상 없으면 상장폐지로 판단
        for unique_key in stock_amounts.keys():
            # 현재 가격이 있으면 마지막 유효 가격 갱신
            if unique_key in current_prices:
                last_valid_prices[unique_key] = current_prices[unique_key]
                last_price_date[unique_key] = current_date.date()
                if unique_key in delisted_stocks:
                    # 상장 복원? (재상장 케이스)
                    self.logger.info(f"{unique_key} 가격 데이터 재등장 (재상장?), 상장폐지 상태 해제")
                    delisted_stocks.remove(unique_key)
            else:
                # 현재 가격이 없을 때
                if unique_key in last_price_date:
                    days_without_price = (current_date.date() - last_price_date[unique_key]).days
                    if days_without_price >= TradingThresholds.DELISTING_THRESHOLD_DAYS and unique_key not in delisted_stocks:
                        # 상장폐지로 판단
                        symbol = dca_info[unique_key]['symbol']
                        self.logger.warning(
                            f"{symbol} ({unique_key}) 상장폐지 감지: "
                            f"마지막 가격 날짜 {last_price_date[unique_key]}, "
                            f"{days_without_price}일간 가격 데이터 없음. "
                            f"마지막 유효 가격 ${last_valid_prices[unique_key]:.2f} 유지"
                        )
                        delisted_stocks.add(unique_key)

        # 상장폐지된 종목의 가격을 마지막 유효 가격으로 유지
        for unique_key in delisted_stocks:
            if unique_key in last_valid_prices and unique_key not in current_prices:
                current_prices[unique_key] = last_valid_prices[unique_key]

    def fetch_and_convert_prices(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, Dict],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        포트폴리오 데이터에서 가격을 추출하고 USD로 변환합니다.

        Args:
            current_date: 현재 시뮬레이션 날짜
            stock_amounts: 종목별 투자 금액
            portfolio_data: 종목별 OHLC 데이터
            dca_info: 종목 정보
            ticker_currencies: 종목별 통화 코드
            exchange_rates_by_currency: 통화별 환율 데이터

        Returns:
            (현재 가격, 마지막 유효 환율) 튜플
        """
        current_prices = {}
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
                        # 이미 USD
                        current_prices[unique_key] = raw_price
                    elif currency in exchange_rates_by_currency:
                        # 환율 데이터가 있는 통화
                        currency_rates = exchange_rates_by_currency[currency]
                        exchange_rate = currency_rates.get(current_date.date())

                        # Fallback
                        if not exchange_rate or exchange_rate <= 0:
                            if currency in last_valid_exchange_rates:
                                exchange_rate = last_valid_exchange_rates[currency]
                                self.logger.warning(
                                    f"{currency} {current_date.date()} 환율 없음, "
                                    f"캐시된 환율 사용: {exchange_rate:.2f}"
                                )
                            else:
                                self.logger.error(
                                    f"{currency} {current_date.date()} 환율 데이터 없음"
                                )
                                continue

                        if exchange_rate and exchange_rate > 0:
                            multiplier = currency_converter.get_conversion_multiplier(
                                currency, exchange_rate
                            )
                            converted_price = raw_price * multiplier

                            self.logger.debug(
                                f"{symbol} 가격 변환: {currency} {raw_price:.2f} -> "
                                f"${converted_price:.2f} (환율: {exchange_rate:.2f})"
                            )
                            current_prices[unique_key] = converted_price
                            last_valid_exchange_rates[currency] = exchange_rate
                    else:
                        # 지원하지 않는 통화
                        self.logger.warning(
                            f"{symbol} 지원하지 않는 통화 {currency}, "
                            f"변환 없이 사용"
                        )
                        current_prices[unique_key] = raw_price

        return current_prices, last_valid_exchange_rates

    def calculate_daily_metrics_and_history(
        self,
        current_date: pd.Timestamp,
        shares: Dict[str, float],
        available_cash: float,
        current_prices: Dict[str, float],
        cash_holdings: Dict[str, float],
        prev_portfolio_value: float,
        daily_cash_inflow: float,
        total_amount: float,
        dca_info: Dict[str, Dict]
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        일일 포트폴리오 가치, 수익률, 비중을 계산합니다.

        Args:
            current_date: 현재 시뮬레이션 날짜
            shares: 종목별 보유 주식 수
            available_cash: 사용 가능한 현금
            current_prices: 종목별 현재 가격
            cash_holdings: 현금 자산별 보유액
            prev_portfolio_value: 이전 날짜 포트폴리오 가치
            daily_cash_inflow: 당일 추가 투자금
            total_amount: 초기 총 투자 금액
            dca_info: 종목 정보

        Returns:
            (정규화된 포트폴리오 가치, 일일 수익률, 현재 비중) 튜플
        """
        # 포트폴리오 가치 계산
        current_portfolio_value = available_cash
        for unique_key in shares.keys():
            if unique_key in current_prices:
                current_portfolio_value += shares[unique_key] * current_prices[unique_key]

        # 포트폴리오 비중 기록
        current_weights = {'date': current_date.strftime('%Y-%m-%d')}
        if current_portfolio_value > 0:
            # 주식 비중
            for unique_key in shares.keys():
                if unique_key in current_prices:
                    stock_value = shares[unique_key] * current_prices[unique_key]
                    symbol = dca_info[unique_key]['symbol']
                    current_weights[symbol] = (
                        current_weights.get(symbol, 0) +
                        stock_value / current_portfolio_value
                    )
            # 현금 비중
            for unique_key, amount in cash_holdings.items():
                symbol = dca_info[unique_key]['symbol']
                current_weights[symbol] = (
                    current_weights.get(symbol, 0) +
                    amount / current_portfolio_value
                )

        # 수익률 계산 (추가 투자금 제외)
        if prev_portfolio_value > 0:
            net_change = (
                current_portfolio_value - prev_portfolio_value - daily_cash_inflow
            )
            daily_return = net_change / prev_portfolio_value
        else:
            daily_return = 0.0

        # 정규화된 포트폴리오 가치
        normalized_value = current_portfolio_value / total_amount

        return normalized_value, daily_return, current_weights
