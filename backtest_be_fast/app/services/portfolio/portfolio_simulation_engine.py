"""포트폴리오 시뮬레이션 엔진 (Engine)

이 모듈은 '작업자' 역할로서 실제 날짜별 시뮬레이션 루프를 수행합니다.
매일의 시장 데이터(가격, 환율)를 처리하고 DCA 매수, 리밸런싱, 상장폐지 등의 핵심 로직을 실행합니다.
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


class PortfolioSimulationEngine:
    """
    포트폴리오 시뮬레이션 엔진 클래스 (Worker/Engine Role)

    [역할 정의]
    이 클래스는 '작업자'로서 **실제 날짜별 시뮬레이션(루프)**을 수행합니다.
    Manager가 준비해준 데이터를 바탕으로 매일의 상태 변화를 계산합니다.

    주요 책임:
    1. Daily Loop: 매일의 시장 변화(가격 변동)를 반영.
    2. Core Logic: DCA 매수, 리밸런싱, 상장폐지 처리 등 핵심 계산 로직 수행.
    3. State Management: 포트폴리오의 일별 평가액, 보유 주식 수 등 상태 갱신.
    """

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

    async def execute_simulation(
        self,
        date_range: pd.DatetimeIndex,
        start_date_obj: datetime,
        end_date_obj: datetime,
        stock_amounts: Dict[str, float],
        amounts: Dict[str, float],
        cash_amount: float,
        total_amount: float,
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, Dict],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]],
        rebalance_frequency: str,
        commission: float
    ) -> pd.DataFrame:
        """
        전체 시뮬레이션 루프를 실행합니다.
        
        Args:
            date_range: 시뮬레이션 날짜 범위
            start_date_obj: 시작 날짜 객체
            end_date_obj: 종료 날짜 객체
            stock_amounts: 주식 종목별 투자 금액
            amounts: 전체 자산 금액
            cash_amount: 초기 현금
            total_amount: 총 투자 금액
            portfolio_data: 포트폴리오 데이터
            dca_info: DCA 정보
            ticker_currencies: 티커별 통화
            exchange_rates_by_currency: 환율 데이터
            rebalance_frequency: 리밸런싱 주기
            commission: 수수료율
            
        Returns:
            시뮬레이션 결과 DataFrame
        """
        # 1. 상태 초기화
        state = self.initialize_portfolio_state(
            stock_amounts=stock_amounts,
            cash_amount=cash_amount,
            amounts=amounts,
            dca_info=dca_info
        )

        shares = state['shares']
        portfolio_values = state['portfolio_values']
        daily_returns = state['daily_returns']
        prev_portfolio_value = state['prev_portfolio_value']
        prev_date = state['prev_date']
        is_first_day = state['is_first_day']
        available_cash = state['available_cash']
        cash_holdings = state['cash_holdings']
        total_trades = state['total_trades']
        rebalance_history = state['rebalance_history']
        weight_history = state['weight_history']
        last_rebalance_date = state['last_rebalance_date']
        original_rebalance_nth = state['original_rebalance_nth']
        last_valid_prices = state['last_valid_prices']
        last_price_date = state['last_price_date']
        delisted_stocks = state['delisted_stocks']

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        # 2. 메인 루프 실행
        for current_date in date_range:
            daily_cash_inflow = 0.0  # 당일 추가 투자금 (DCA)
            if current_date.date() < start_date_obj.date():
                continue
            if current_date.date() > end_date_obj.date():
                break

            # 2.1 가격 조회 및 환율 변환
            current_prices, last_valid_exchange_rates = self.fetch_and_convert_prices(
                current_date=current_date,
                stock_amounts=stock_amounts,
                portfolio_data=portfolio_data,
                dca_info=dca_info,
                ticker_currencies=ticker_currencies,
                exchange_rates_by_currency=exchange_rates_by_currency
            )

            # 2.2 상장폐지 감지
            self.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices=current_prices,
                dca_info=dca_info,
                delisted_stocks=delisted_stocks,
                last_valid_prices=last_valid_prices,
                last_price_date=last_price_date
            )

            # 2.3 리밸런싱 로깅 (상장폐지 관련)
            # should_rebalance 계산 전이지만, delisted 로깅을 위해 위치 유지
            # 다만 should_rebalance 값은 아래에서 계산되므로 여기서는 단순히 월요일 체크로 대체하거나
            # 정확한 로직 순서를 위해 아래로 이동이 좋으나, 기존 로직 유지를 위해 필요한 변수 미리 계산

            # 리밸런싱 조건 확인을 위한 Nth값 설정
            if original_rebalance_nth is None and rebalance_frequency != 'none':
                original_rebalance_nth = get_weekday_occurrence(start_date_obj)
                self.logger.debug(f"리밸런싱 원본 Nth 값 설정 = {original_rebalance_nth}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            should_rebalance = RebalanceHelper.is_rebalance_date(
                current_date, prev_date, rebalance_frequency, start_date_obj, last_rebalance_date, original_rebalance_nth
            )

            if delisted_stocks and (should_rebalance or current_date.weekday() == 0):
                delisted_symbols = [dca_info[key]['symbol'] for key in delisted_stocks if key in dca_info]
                self.logger.info(
                    f"{current_date.date()}: 상장폐지 종목 {len(delisted_stocks)}개 추적 중 "
                    f"[{', '.join(delisted_symbols)}]"
                )

            # 2.4 DCA 실행 (첫날 매수 또는 정기 매수)
            if is_first_day:
                trades, cash_inflow = self.dca_manager.execute_initial_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=shares,
                    commission=commission
                )
                total_trades += trades
                daily_cash_inflow += cash_inflow
                is_first_day = False
                prev_date = current_date

            if prev_date is not None and prev_date != current_date:
                trades, cash_inflow = self.dca_manager.execute_periodic_purchases(
                    current_date=current_date,
                    prev_date=prev_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=shares,
                    commission=commission,
                    start_date_obj=start_date_obj
                )
                total_trades += trades
                daily_cash_inflow += cash_inflow


            # 2.5 리밸런싱 실행
            if rebalance_frequency != 'none':
                if should_rebalance and len(target_weights) > 1:
                    self.logger.info(
                        f"{current_date.date()}: 리밸런싱 트리거됨 "
                        f"(주기: {rebalance_frequency}, 자산 수: {len(target_weights)}, "
                        f"마지막 리밸런싱: {last_rebalance_date.date() if last_rebalance_date else '없음'})"
                    )
                elif should_rebalance and len(target_weights) <= 1:
                    self.logger.debug(
                        f"{current_date.date()}: 리밸런싱 조건 충족하지만 자산 수 부족 (자산 수: {len(target_weights)})"
                    )

            if should_rebalance and len(target_weights) > 1:
                adjusted_target_weights = self.rebalancer.calculate_adjusted_weights(
                    target_weights=target_weights,
                    delisted_stocks=delisted_stocks,
                    dca_info=dca_info
                )

                if delisted_stocks:
                    for unique_key, adj_weight in adjusted_target_weights.items():
                        if unique_key not in delisted_stocks:
                            original_weight = target_weights.get(unique_key, 0.0)
                            if original_weight != adj_weight:
                                symbol = dca_info[unique_key]['symbol']
                                self.logger.debug(
                                    f"  {symbol}: {original_weight:.2%} -> {adj_weight:.2%}"
                                )

                total_stock_value = sum(
                    shares[key] * current_prices.get(key, 0)
                    for key in shares.keys()
                    if key in current_prices
                )

                rebalance_result = self.rebalancer.execute_rebalancing_trades(
                    current_date=current_date,
                    adjusted_target_weights=adjusted_target_weights,
                    shares=shares,
                    current_prices=current_prices,
                    available_cash=available_cash,
                    cash_holdings=cash_holdings,
                    commission=commission,
                    total_stock_value=total_stock_value,
                    dca_info=dca_info,
                    delisted_stocks=delisted_stocks
                )

                shares = rebalance_result['updated_shares']
                cash_holdings = rebalance_result['updated_cash_holdings']
                available_cash = rebalance_result['updated_available_cash']
                trades_in_rebalance = rebalance_result['trades_executed']

                if rebalance_result['rebalance_trades']:
                    rebalance_history.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'trades': rebalance_result['rebalance_trades'],
                        'weights_before': rebalance_result['weights_before'],
                        'weights_after': rebalance_result['weights_after'],
                        'commission_cost': rebalance_result['commission_cost']
                    })

                last_rebalance_date = current_date
                total_trades += trades_in_rebalance

            # 2.6 메트릭 계산
            # metrics 인스턴스가 필요함. PortfolioService에서 주입받거나 여기서 생성해야 함.
            # 하지만 PortfolioSimulator는 metrics 속성을 가지고 있지 않음.
            # 방법 1: initialize에서 PortfolioMetrics 생성
            # 방법 2: 인자로 받기
            # 여기서는 편의상 내부에서 import해서 사용하거나, 기존 service에 있는 metrics를 사용해야 하는데
            # PortfolioMetrics는 별도 상태가 없으므로 여기서 매번 생성하거나 class member로 두는게 좋음.
            # 상단 import 확인: from app.services.portfolio.portfolio_metrics import PortfolioMetrics (없으면 추가 필요)
            
            # (import 추가 필요, 아래에서 처리)
            from app.services.portfolio.portfolio_metrics import PortfolioMetrics
            metrics_calculator = PortfolioMetrics()

            normalized_value, daily_return, current_weights = metrics_calculator.calculate_daily_metrics_and_history(
                current_date=current_date,
                shares=shares,
                available_cash=available_cash,
                current_prices=current_prices,
                cash_holdings=cash_holdings,
                prev_portfolio_value=prev_portfolio_value,
                daily_cash_inflow=daily_cash_inflow,
                total_amount=total_amount,
                dca_info=dca_info
            )

            portfolio_values.append(normalized_value)
            daily_returns.append(daily_return)
            weight_history.append(current_weights)

            prev_portfolio_value = normalized_value * total_amount
            prev_date = current_date

        # 3. 결과 정리
        valid_dates = [d for d in date_range if start_date_obj.date() <= d.date() <= end_date_obj.date()]

        if len(portfolio_values) != len(valid_dates):
            self.logger.warning(f"포트폴리오 값 길이 불일치: portfolio_values={len(portfolio_values)}, valid_dates={len(valid_dates)}")
            raise ValueError(f"계산된 포트폴리오 값 개수({len(portfolio_values)})가 날짜 개수({len(valid_dates)})와 일치하지 않습니다.")

        result = pd.DataFrame({
            'Date': valid_dates,
            'Portfolio_Value': portfolio_values,
            'Daily_Return': daily_returns,
            'Cumulative_Return': [(v - 1) * 100 for v in portfolio_values]
        })
        result.set_index('Date', inplace=True)

        result.attrs['total_trades'] = total_trades
        result.attrs['rebalance_history'] = rebalance_history
        result.attrs['weight_history'] = weight_history

        return result
