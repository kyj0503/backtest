"""포트폴리오 시뮬레이션 엔진 (Engine)

이 모듈은 '작업자' 역할로서 실제 날짜별 시뮬레이션 루프를 수행합니다.
매일의 시장 데이터(가격, 환율)를 처리하고 DCA 매수, 리밸런싱, 상장폐지 등의 핵심 로직을 실행합니다.
"""

import logging
from typing import Dict, Tuple
from datetime import datetime, date
import pandas as pd

from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.rebalance_helper import RebalanceHelper, get_weekday_occurrence
from app.utils.currency_converter import currency_converter
from app.constants.data_loading import TradingThresholds
from app.domain.portfolio_domain import DcaStrategyInfo, PortfolioState
from app.services.portfolio.portfolio_metrics import PortfolioMetrics

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
        포트폴리오 시뮬레이션 엔진 초기화

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
        dca_info: Dict[str, DcaStrategyInfo]
    ) -> PortfolioState:
        """
        포트폴리오 시뮬레이션을 위한 모든 추적 변수를 초기화합니다.

        Args:
            stock_amounts: 주식 종목별 투자 금액
            cash_amount: 총 현금 금액
            amounts: 전체 자산 금액 (주식 + 현금)
            dca_info: 분할 매수 정보

        Returns:
            초기화된 PortfolioState 객체
        """
        return PortfolioState(
            shares={key: 0.0 for key in stock_amounts.keys()},
            available_cash=cash_amount,
            cash_holdings={k: v for k, v in amounts.items() if dca_info[k].asset_type == 'cash'},
            delisted_stocks=set(),
            pending_initial_keys=set(stock_amounts.keys())
        )

    def detect_and_update_delisting(
        self,
        current_date: pd.Timestamp,
        stock_amounts: Dict[str, float],
        current_prices: Dict[str, float],
        dca_info: Dict[str, DcaStrategyInfo],
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
                        symbol = dca_info[unique_key].symbol
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

    def _pre_calculate_prices(
        self,
        date_range: pd.DatetimeIndex,
        stock_amounts: Dict[str, float],
        portfolio_data: Dict[str, pd.DataFrame],
        dca_info: Dict[str, DcaStrategyInfo],
        ticker_currencies: Dict[str, str],
        exchange_rates_by_currency: Dict[str, Dict[date, float]]
    ) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
        """
        [성능 최적화] 시뮬레이션 기간 동안의 모든 가격 데이터를 미리 정렬(Pre-align) 및 계산합니다.
        
        기존 로직(매일 슬라이싱)의 O(N^2) 복잡도를 O(N)으로 줄이기 위해 사용됩니다.
        - 각 종목의 데이터를 date_range에 맞춰 Reindex
        - Forward Fill로 결측치(휴장일 등) 채움
        - 환율 변환 미리 적용 (가능한 경우)

        Returns:
            aligned_prices: {ticker: Series(adjusted_price, index=date_range)}
            aligned_exchange_rates: {currency: Series(rate, index=date_range)}
        """
        aligned_prices = {}
        aligned_exchange_rates = {}

        # 1. 환율 데이터 정렬
        # (통화별로 미리 Series 생성)
        for currency, rates_map in exchange_rates_by_currency.items():
            if not rates_map:
                continue
            # date -> datetime64 변환을 위해 DataFrame/Series 생성
            rates_series = pd.Series(rates_map)
            rates_series.index = pd.to_datetime(rates_series.index)
            
            # Reindex & FFill
            # [Copilot Suggestion] ffill만 하면 시뮬레이션 시작일보다 환율 데이터가 늦게 시작될 경우 앞부분이 NaN이 됨.
            # bfill을 추가하여 앞부분 결측치도 보완 (최초 환율로 메꿈)
            aligned_rate = rates_series.reindex(date_range).ffill().bfill()
            aligned_exchange_rates[currency] = aligned_rate

        # 2. 주가 데이터 정렬 & 환율 적용
        for unique_key in stock_amounts.keys():
            symbol = dca_info[unique_key].symbol
            if symbol not in portfolio_data:
                continue

            df = portfolio_data[symbol]
            # 인덱스가 이미 datetime이어야 함
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)

            # Close 가격만 추출 및 정렬
            price_series = df['Close'].reindex(date_range).ffill()

            # 환율 변환
            currency = ticker_currencies.get(unique_key, 'USD')
            if currency != 'USD' and currency in aligned_exchange_rates:
                # 벡터 연산으로 전체 기간 환율 적용
                # [Copilot Suggestion] 벡터 연산 (환율 적용) - apply 제거 및 Vectorization 적용
                exchange_rates = aligned_exchange_rates[currency]
                
                # 주요 통화(EUR, GBP 등)는 직접 곱하기, 그 외(KRW, JPY 등)는 나누기 역수
                # CurrencyConverter.get_conversion_multiplier 로직을 벡터화
                if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
                     # Direct multiplication
                     price_series = price_series * exchange_rates
                else:
                     # Inverse (1 / rate)
                     # 0 또는 NaN인 경우 1.0으로 처리 (Division by Zero 방지)
                     valid_mask = (exchange_rates > 0) & (pd.notnull(exchange_rates))
                     multipliers = pd.Series(1.0, index=exchange_rates.index)
                     multipliers[valid_mask] = 1.0 / exchange_rates[valid_mask]
                     
                     price_series = price_series * multipliers
            elif currency != 'USD':
                # [Copilot Suggestion] 지원하지 않는 통화 경고 로그 복원
                # (USD가 아닌데 exchange_rates에 없는 경우)
                self.logger.warning(
                    f"{symbol} ({unique_key}) 지원하지 않는 통화 '{currency}' 또는 환율 데이터 누락. "
                    f"변환 없이 원본 가격 사용."
                )
            
            aligned_prices[unique_key] = price_series

        return aligned_prices, aligned_exchange_rates

    def _get_daily_prices_from_aligned(
        self,
        current_date: pd.Timestamp,
        aligned_prices: Dict[str, pd.Series],
        aligned_exchange_rates: Dict[str, pd.Series],
        ticker_currencies: Dict[str, str],
        last_valid_exchange_rates: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        [성능 최적화] 미리 계산된 데이터에서 O(1)로 당일 가격 조회
        """
        current_prices = {}
        
        # 1. 환율 캐시 업데이트
        for currency, rates_series in aligned_exchange_rates.items():
            try:
                rate = rates_series.at[current_date]
                if pd.notnull(rate):
                    last_valid_exchange_rates[currency] = rate
            except KeyError:
                pass # 해당 통화의 환율 데이터가 없는 날짜는 캐시 갱신 없이 진행

        # 2. 가격 조회
        for unique_key, price_series in aligned_prices.items():
            try:
                price = price_series.at[current_date]
                # NaN 체크 (해당 날짜 데이터 없음 or 상장폐지 등)
                if pd.notnull(price):
                    current_prices[unique_key] = float(price)
            except KeyError:
                pass # 배열에 해당 날짜 데이터가 없으면 스킵 (상장폐지, 휴장일 등)
                
        return current_prices, last_valid_exchange_rates


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
        dca_info: Dict[str, DcaStrategyInfo],
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
            dca_info: DCA 정보 (DcaStrategyInfo 모델)
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

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        # [성능 최적화] 데이터 미리 준비 (Vectorization)
        aligned_prices, aligned_exchange_rates = self._pre_calculate_prices(
            date_range, stock_amounts, portfolio_data, dca_info, ticker_currencies, exchange_rates_by_currency
        )
        last_valid_exchange_rates = {} # 루프 내 캐싱용

        # 2. 메인 루프 실행
        for current_date in date_range:
            daily_cash_inflow = 0.0  # 당일 추가 투자금 (DCA)
            if current_date.date() < start_date_obj.date():
                continue
            if current_date.date() > end_date_obj.date():
                break

            # 2.1 가격 조회 (최적화 버전)
            current_prices, last_valid_exchange_rates = self._get_daily_prices_from_aligned(
                current_date=current_date,
                aligned_prices=aligned_prices,
                aligned_exchange_rates=aligned_exchange_rates,
                ticker_currencies=ticker_currencies,
                last_valid_exchange_rates=last_valid_exchange_rates
            )

            # 2.2 상장폐지 감지
            self.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices=current_prices,
                dca_info=dca_info,
                delisted_stocks=state.delisted_stocks,
                last_valid_prices=state.last_valid_prices,
                last_price_date=state.last_price_date
            )

            # 2.3 리밸런싱 로깅 (상장폐지 관련)
            if state.original_rebalance_nth is None and rebalance_frequency != 'none':
                state.original_rebalance_nth = get_weekday_occurrence(start_date_obj)
                self.logger.debug(f"리밸런싱 원본 Nth 값 설정 = {state.original_rebalance_nth}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            should_rebalance = RebalanceHelper.is_rebalance_date(
                current_date, state.prev_date, rebalance_frequency, start_date_obj, state.last_rebalance_date, state.original_rebalance_nth
            )

            if state.delisted_stocks and (should_rebalance or current_date.weekday() == 0):
                delisted_symbols = [dca_info[key].symbol for key in state.delisted_stocks if key in dca_info]
                self.logger.info(
                    f"{current_date.date()}: 상장폐지 종목 {len(state.delisted_stocks)}개 추적 중 "
                    f"[{', '.join(delisted_symbols)}]"
                )

            # 2.4 DCA 실행 (초기 매수 또는 정기 매수)
            #
            # 초기 매수는 "첫날 한 번"이 아니라 "각 종목이 처음 가격을 갖는 날"에
            # 이뤄져야 한다. 혼합 시장 포트폴리오에서는 시작일에 한쪽 시장이
            # 휴장이라 가격이 없을 수 있는데, 과거에는 그 종목을 건너뛴 뒤 다시
            # 시도하지 않아 포지션이 영영 열리지 않고 투자금만 분모에 남았다.
            if state.pending_initial_keys:
                trades, cash_inflow = self.dca_manager.execute_initial_purchases(
                    current_date=current_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=state.shares,
                    commission=commission,
                    pending_keys=state.pending_initial_keys
                )
                state.total_trades += trades
                daily_cash_inflow += cash_inflow

            if state.is_first_day:
                state.is_first_day = False
                state.prev_date = current_date

            if state.prev_date is not None and state.prev_date != current_date:
                trades, cash_inflow = self.dca_manager.execute_periodic_purchases(
                    current_date=current_date,
                    prev_date=state.prev_date,
                    stock_amounts=stock_amounts,
                    current_prices=current_prices,
                    dca_info=dca_info,
                    shares=state.shares,
                    commission=commission,
                    start_date_obj=start_date_obj
                )
                state.total_trades += trades
                daily_cash_inflow += cash_inflow


            # 2.5 리밸런싱 실행
            if rebalance_frequency != 'none':
                if should_rebalance and len(target_weights) > 1:
                    last_rebal_str = state.last_rebalance_date.strftime('%Y-%m-%d') if state.last_rebalance_date else '없음'
                    self.logger.info(
                        f"{current_date.date()}: 리밸런싱 트리거됨 "
                        f"(주기: {rebalance_frequency}, 자산 수: {len(target_weights)}, "
                        f"마지막 리밸런싱: {last_rebal_str})"
                    )
                elif should_rebalance and len(target_weights) <= 1:
                    self.logger.debug(
                        f"{current_date.date()}: 리밸런싱 조건 충족하지만 자산 수 부족 (자산 수: {len(target_weights)})"
                    )

            if should_rebalance and len(target_weights) > 1:
                adjusted_target_weights = self.rebalancer.calculate_adjusted_weights(
                    target_weights=target_weights,
                    delisted_stocks=state.delisted_stocks,
                    dca_info=dca_info
                )

                if state.delisted_stocks:
                    for unique_key, adj_weight in adjusted_target_weights.items():
                        if unique_key not in state.delisted_stocks:
                            original_weight = target_weights.get(unique_key, 0.0)
                            if original_weight != adj_weight:
                                symbol = dca_info[unique_key].symbol
                                self.logger.debug(
                                    f"  {symbol}: {original_weight:.2%} -> {adj_weight:.2%}"
                                )

                total_stock_value = sum(
                    state.shares[key] * current_prices.get(key, 0)
                    for key in state.shares.keys()
                    if key in current_prices
                )

                rebalance_result = self.rebalancer.execute_rebalancing_trades(
                    current_date=current_date,
                    adjusted_target_weights=adjusted_target_weights,
                    shares=state.shares,
                    current_prices=current_prices,
                    available_cash=state.available_cash,
                    cash_holdings=state.cash_holdings,
                    commission=commission,
                    total_stock_value=total_stock_value,
                    dca_info=dca_info,
                    delisted_stocks=state.delisted_stocks
                )

                state.shares = rebalance_result['updated_shares']
                state.cash_holdings = rebalance_result['updated_cash_holdings']
                state.available_cash = rebalance_result['updated_available_cash']
                trades_in_rebalance = rebalance_result['trades_executed']

                if rebalance_result['rebalance_trades']:
                    state.rebalance_history.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'trades': rebalance_result['rebalance_trades'],
                        'weights_before': rebalance_result['weights_before'],
                        'weights_after': rebalance_result['weights_after'],
                        'commission_cost': rebalance_result['commission_cost']
                    })

                state.last_rebalance_date = current_date.date()
                state.total_trades += trades_in_rebalance

            # 2.6 메트릭 계산
            metrics_calculator = PortfolioMetrics()

            normalized_value, daily_return, current_weights = metrics_calculator.calculate_daily_metrics_and_history(
                current_date=current_date,
                shares=state.shares,
                available_cash=state.available_cash,
                current_prices=current_prices,
                cash_holdings=state.cash_holdings,
                prev_portfolio_value=state.prev_portfolio_value,
                daily_cash_inflow=daily_cash_inflow,
                total_amount=total_amount,
                dca_info=dca_info
            )

            state.portfolio_values.append(normalized_value)
            state.daily_returns.append(daily_return)
            state.weight_history.append(current_weights)

            state.prev_portfolio_value = normalized_value * total_amount
            state.prev_date = current_date

        # 3. 결과 정리
        valid_dates = [d for d in date_range if start_date_obj.date() <= d.date() <= end_date_obj.date()]

        if len(state.portfolio_values) != len(valid_dates):
            self.logger.warning(f"포트폴리오 값 길이 불일치: portfolio_values={len(state.portfolio_values)}, valid_dates={len(valid_dates)}")
            # 길이를 맞추거나 에러를 던지는데, 여기선 에러
            # (기존 로직 유지)

        result = pd.DataFrame({
            'Date': valid_dates,
            'Portfolio_Value': state.portfolio_values,
            'Daily_Return': state.daily_returns,
            'Cumulative_Return': [(v - 1) * 100 for v in state.portfolio_values]
        })
        result.set_index('Date', inplace=True)

        result.attrs['total_trades'] = state.total_trades
        result.attrs['rebalance_history'] = state.rebalance_history
        result.attrs['weight_history'] = state.weight_history

        return result
