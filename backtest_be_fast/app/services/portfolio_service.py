"""포트폴리오 백테스트 서비스

여러 종목으로 구성된 포트폴리오의 백테스트를 실행합니다.
DCA(분할 매수), 리밸런싱, 다중 통화를 지원합니다.

통화 정책:
- DB 저장: 원본 통화 (KRW, JPY, EUR 등)
- 백테스트 계산: 모든 가격을 USD로 변환
- 프론트엔드: 개별 종목은 원본 통화, 결과는 USD
"""
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from datetime import datetime, timedelta, date
import logging

from app.schemas.schemas import PortfolioBacktestRequest, FREQUENCY_MAP
from app.schemas.requests import BacktestRequest
from app.services.backtest_service import backtest_service
from app.repositories.stock_repository import get_stock_repository
from app.services.dca_calculator import DcaCalculator
from app.services.rebalance_helper import RebalanceHelper, get_next_nth_weekday, get_weekday_occurrence
from app.services.portfolio_calculator_service import portfolio_calculator
from app.services.portfolio.portfolio_dca_manager import PortfolioDcaManager
from app.services.portfolio.portfolio_rebalancer import PortfolioRebalancer
from app.services.portfolio.portfolio_simulator import PortfolioSimulator
from app.services.portfolio.portfolio_metrics import PortfolioMetrics
from app.utils.serializers import recursive_serialize
from app.core.exceptions import (
    DataNotFoundError,
    InvalidSymbolError,
    ValidationError
)
from app.constants.currencies import SUPPORTED_CURRENCIES, EXCHANGE_RATE_LOOKBACK_DAYS
from app.constants.data_loading import TradingThresholds
from app.utils.currency_converter import currency_converter

logger = logging.getLogger(__name__)

class PortfolioService:
    """포트폴리오 백테스트 서비스"""
    def __init__(self):
        """포트폴리오 서비스 초기화"""
        # 추출된 컴포넌트 초기화
        self.dca_manager = PortfolioDcaManager()
        self.rebalancer = PortfolioRebalancer()
        self.simulator = PortfolioSimulator(
            dca_manager=self.dca_manager,
            rebalancer=self.rebalancer
        )
        self.metrics = PortfolioMetrics()
        # Repository 초기화 (Repository 패턴)
        self.stock_repository = get_stock_repository()
        logger.info("포트폴리오 서비스가 초기화되었습니다")

    async def calculate_dca_portfolio_returns(
        self,
        portfolio_data: Dict[str, pd.DataFrame],
        amounts: Dict[str, float],
        dca_info: Dict[str, Dict],
        start_date: str,
        end_date: str,
        rebalance_frequency: str = "weekly_4",
        commission: float = 0.0
    ) -> pd.DataFrame:
        """DCA와 리밸런싱을 고려한 포트폴리오 수익률 계산

        Note: last_rebalance_date는 예정일 추적용, rebalance_history는 실제 거래만 기록
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

        # 각 종목의 currency 정보 먼저 가져오기 (배치 조회로 최적화)
        symbols = [dca_info[unique_key]['symbol'] for unique_key in stock_amounts.keys()]
        try:
            ticker_info_dict = await asyncio.to_thread(
                self.stock_repository.get_tickers_info_batch, symbols
            )
            ticker_currencies = {}
            for unique_key in stock_amounts.keys():
                symbol = dca_info[unique_key]['symbol']
                ticker_info = ticker_info_dict.get(symbol, {})
                ticker_currencies[unique_key] = ticker_info.get('currency', 'USD')
                logger.debug(f"{symbol} currency: {ticker_currencies[unique_key]}")
        except Exception as e:
            logger.warning(f"티커 정보 배치 조회 실패: {e}, 모두 USD로 가정")
            ticker_currencies = {unique_key: 'USD' for unique_key in stock_amounts.keys()}

        required_currencies = list(set(ticker_currencies.values()) - {'USD'})

        if required_currencies:
            logger.info(f"포트폴리오 환율 로딩 시작: {len(required_currencies)}개 통화 [{', '.join(required_currencies)}]")

        exchange_rates_by_currency = await currency_converter.load_multiple_exchange_rates(
            currencies=required_currencies,
            start_date=start_date,
            end_date=end_date,
            date_range=date_range,
            buffer_multiplier=2  # EXCHANGE_RATE_LOOKBACK_DAYS * 2
        )

        # 환율 로드 결과 요약 로깅
        if required_currencies:
            for currency, rates in exchange_rates_by_currency.items():
                if rates:
                    rate_values = list(rates.values())
                    rate_min = min(rate_values)
                    rate_max = max(rate_values)
                    rate_mean = sum(rate_values) / len(rate_values)
                    logger.info(
                        f"환율 로드 완료 ({currency}): {len(rates)} 포인트, "
                        f"범위 {rate_min:.4f} ~ {rate_max:.4f} (평균 {rate_mean:.4f})"
                    )
                else:
                    logger.warning(f"환율 데이터 없음 ({currency}): 변환 불가")
            logger.info(f"총 {len(exchange_rates_by_currency)}/{len(required_currencies)}개 통화 환율 로드 완료")

        target_weights = RebalanceHelper.calculate_target_weights(amounts, dca_info)

        state = self.simulator.initialize_portfolio_state(
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

        for current_date in date_range:
            daily_cash_inflow = 0.0  # 당일 추가 투자금 (DCA)
            if current_date.date() < start_date_obj.date():
                continue
            if current_date.date() > end_date_obj.date():
                break

            current_prices, last_valid_exchange_rates = self.simulator.fetch_and_convert_prices(
                current_date=current_date,
                stock_amounts=stock_amounts,
                portfolio_data=portfolio_data,
                dca_info=dca_info,
                ticker_currencies=ticker_currencies,
                exchange_rates_by_currency=exchange_rates_by_currency
            )

            self.simulator.detect_and_update_delisting(
                current_date=current_date,
                stock_amounts=stock_amounts,
                current_prices=current_prices,
                dca_info=dca_info,
                delisted_stocks=delisted_stocks,
                last_valid_prices=last_valid_prices,
                last_price_date=last_price_date
            )

            if delisted_stocks and (should_rebalance or current_date.weekday() == 0):
                delisted_symbols = [dca_info[key]['symbol'] for key in delisted_stocks if key in dca_info]
                logger.info(
                    f"{current_date.date()}: 상장폐지 종목 {len(delisted_stocks)}개 추적 중 "
                    f"[{', '.join(delisted_symbols)}]"
                )

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

            if prev_date is not None:
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

            if original_rebalance_nth is None and rebalance_frequency != 'none':
                original_rebalance_nth = get_weekday_occurrence(start_date_obj)
                logger.debug(f"리밸런싱 원본 Nth 값 설정 = {original_rebalance_nth}번째 {['월','화','수','목','금','토','일'][start_date_obj.weekday()]}요일")

            should_rebalance = RebalanceHelper.is_rebalance_date(
                current_date, prev_date, rebalance_frequency, start_date_obj, last_rebalance_date, original_rebalance_nth
            )

            if rebalance_frequency != 'none':
                if should_rebalance and len(target_weights) > 1:
                    logger.info(
                        f"{current_date.date()}: 리밸런싱 트리거됨 "
                        f"(주기: {rebalance_frequency}, 자산 수: {len(target_weights)}, "
                        f"마지막 리밸런싱: {last_rebalance_date.date() if last_rebalance_date else '없음'})"
                    )
                elif should_rebalance and len(target_weights) <= 1:
                    logger.debug(
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
                                logger.debug(
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

            normalized_value, daily_return, current_weights = self.metrics.calculate_daily_metrics_and_history(
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

        valid_dates = [d for d in date_range if start_date_obj.date() <= d.date() <= end_date_obj.date()]

        if len(portfolio_values) != len(valid_dates):
            logger.warning(f"포트폴리오 값 길이 불일치: portfolio_values={len(portfolio_values)}, valid_dates={len(valid_dates)}")
            logger.warning(f"첫 3개 날짜: {valid_dates[:3] if len(valid_dates) > 0 else 'None'}")
            logger.warning(f"마지막 3개 날짜: {valid_dates[-3:] if len(valid_dates) > 0 else 'None'}")
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
            start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
            duration_days = (end_date_obj - start_date_obj).days

            # 연간 수익률 계산
            annual_return = ((total_portfolio_value / total_amount) ** (365.25 / duration_days) - 1) * 100 if duration_days > 0 else 0

            # 먼저 equity curve, daily returns, weight history 계산
            equity_curve, daily_returns, weight_history = await portfolio_calculator._calculate_realistic_equity_curve(
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

            # 백테스트 기간 계산 (주 수)
            start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')

            # 백테스트 기간을 주 단위로 계산
            backtest_days = (end_date_obj - start_date_obj).days
            backtest_weeks = backtest_days // 7  # 주 단위 (정수 나눗셈)

            logger.info(f"백테스트 기간: {request.start_date} ~ {request.end_date} ({backtest_days}일, {backtest_weeks}주)")

            # 분할 매수 정보 수집 및 총 투자 금액 계산
            dca_info = {}
            cash_amount = 0

            # Phase 1: 먼저 모든 종목의 투자 타입을 확인하고 dca_info 설정
            symbols_to_load = []  # 데이터를 로드할 종목 리스트

            for item in request.portfolio:
                symbol = item.symbol
                investment_type = getattr(item, 'investment_type', 'lump_sum')
                dca_frequency = getattr(item, 'dca_frequency', 'monthly_1')

                # DCA 투자 횟수 계산 (Nth Weekday 방식)
                if investment_type == 'dca':
                    period_info = FREQUENCY_MAP.get(dca_frequency, FREQUENCY_MAP['monthly_1'])
                    period_type, interval = period_info

                    # 근사 계산으로 DCA 횟수 추정
                    if period_type == 'weekly':
                        approx_days_per_period = interval * 7
                    elif period_type == 'monthly':
                        approx_days_per_period = interval * 30  # 월 평균 30일
                    else:
                        approx_days_per_period = 30

                    # 백테스트 기간 동안 몇 번 투자할지 계산
                    dca_periods = max(1, (backtest_days // approx_days_per_period) + 1)
                else:
                    dca_periods = 1

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
                    'monthly_amount': per_period_amount,  # 회당 투자 금액
                    'asset_type': asset_type,
                    'executed_count': 0,  # 실행된 DCA 횟수 추적
                    'last_dca_date': None,  # 마지막 DCA 실행 날짜 추적
                    'original_nth_weekday': None  # 원본 "몇 번째 요일" 값 추적 (일관성 유지용)
                }

                # 진짜 현금 자산 처리 (asset_type이 'cash'인 경우)
                if asset_type == 'cash':
                    # 현금 처리
                    cash_amount += total_investment
                    logger.info(f"현금 자산 {symbol} 추가 (금액: ${total_investment:,.2f})")
                    continue

                logger.info(f"종목 {symbol} 데이터 로드 예정 (총 투자금액: ${total_investment:,.2f}, 방식: {investment_type})")

                if investment_type == 'dca':
                    logger.info(f"분할 매수: {dca_periods}회에 걸쳐 회당 ${per_period_amount:,.2f}씩 (총 ${total_investment:,.2f})")
                    logger.info(f"DCA 설정: frequency={dca_frequency}, dca_periods={dca_periods}")

                # 로드할 종목 리스트에 추가
                symbols_to_load.append(symbol)

            # Phase 2: 모든 종목 데이터를 병렬로 로드 (N+1 query 최적화)
            if symbols_to_load:
                logger.info(f"포트폴리오 데이터 병렬 로드 시작: {len(symbols_to_load)}개 종목")

                # 병렬 로드 태스크 생성
                load_tasks = [
                    asyncio.to_thread(self.stock_repository.load_stock_data, symbol, request.start_date, request.end_date)
                    for symbol in symbols_to_load
                ]

                # 병렬 실행
                load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

                # 결과 처리
                for symbol, result in zip(symbols_to_load, load_results):
                    if isinstance(result, Exception):
                        logger.warning(f"종목 {symbol} 데이터 로드 실패: {result}")
                        continue

                    if result is None or result.empty:
                        logger.warning(f"종목 {symbol}의 데이터가 없습니다.")
                        continue

                    portfolio_data[symbol] = result
                    logger.info(f"종목 {symbol} 데이터 로드 완료: {len(result)} 행")

                logger.info(f"포트폴리오 데이터 병렬 로드 완료: {len(portfolio_data)}/{len(symbols_to_load)}개 성공")

            # 총 투자 금액 계산
            total_amount = sum(amounts.values())
            
            # 현금만 있는 경우 처리
            if not portfolio_data and cash_amount > 0:
                logger.info("현금만 있는 포트폴리오로 백테스트 실행")

                # 현금 전용 결과 생성
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
            portfolio_result = await self.calculate_dca_portfolio_returns(
                portfolio_data, amounts, dca_info, request.start_date, request.end_date,
                request.rebalance_frequency, request.commission
            )
            
            # 통계 계산
            logger.info("포트폴리오 통계 계산 중...")
            statistics = portfolio_calculator.calculate_portfolio_statistics(portfolio_result, total_amount)
            
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
                                'Type': 'BUY',
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
                            # 분할매수: DcaCalculator를 사용하여 수익률 계산
                            dca_periods = dca_info[unique_key]['dca_periods']
                            period_amount = dca_info[unique_key]['monthly_amount']  # 회당 투자 금액
                            dca_frequency = dca_info[unique_key].get('dca_frequency', 'monthly_1')  # DCA 주기

                            total_shares, average_price, individual_return, dca_trade_log = DcaCalculator.calculate_dca_shares_and_return(
                                df, period_amount, dca_periods, request.start_date, dca_frequency
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

            # 리밸런싱 거래를 각 종목의 trade_log에 추가
            for rebalance_event in rebalance_history:
                rebalance_date = rebalance_event['date']
                for trade in rebalance_event['trades']:
                    symbol = trade['symbol']
                    action = trade['action']

                    # unique_key 찾기 (symbol로 매칭)
                    unique_key = None
                    for key in dca_info.keys():
                        if dca_info[key]['symbol'] == symbol:
                            unique_key = key
                            break

                    if unique_key and unique_key in strategy_details:
                        # 거래 타입 결정 (buy/sell만 처리, 현금은 제외)
                        if action in ['buy', 'sell']:
                            trade_entry = {
                                'EntryTime': rebalance_date,
                                'EntryPrice': float(trade['price']),
                                'Size': float(trade['shares']),
                                'Type': 'BUY' if action == 'buy' else 'SELL',
                                'ExitTime': None,
                                'ExitPrice': None,
                                'PnL': None,
                                'ReturnPct': None,
                                'Duration': None,
                            }
                            strategy_details[unique_key]['trade_log'].append(trade_entry)

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
