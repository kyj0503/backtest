"""
포트폴리오 계산 서비스

**역할**:
- 포트폴리오 통계 계산 (샤프 비율, 최대 낙폭 등)
- 포트폴리오 Equity Curve 계산
- 포트폴리오 일일 수익률 및 비중 히스토리 관리

**주요 기능**:
1. calculate_portfolio_statistics(): 백테스트 결과 통계 계산
2. _get_max_consecutive(): 연속된 상승/하락일 계산
3. _calculate_realistic_equity_curve(): 개별 종목 equity curve 합산
4. _fallback_equity_curve(): 데이터 없을 때 선형 equity curve

**의존성**:
- pandas: 시계열 데이터 처리
- numpy: 수치 계산
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from datetime import datetime
import logging

from app.schemas.schemas import PortfolioBacktestRequest

logger = logging.getLogger(__name__)


class PortfolioCalculatorService:
    """포트폴리오 통계 및 Equity Curve 계산 서비스"""

    @staticmethod
    def calculate_portfolio_statistics(portfolio_data: pd.DataFrame, total_amount: float) -> Dict[str, Any]:
        """
        포트폴리오 통계 계산

        Args:
            portfolio_data: Portfolio_Value, Daily_Return 컬럼을 포함한 DataFrame
            total_amount: 초기 투자금

        Returns:
            통계 정보 딕셔너리 (수익률, 샤프 비율, 최대 낙폭 등)
        """
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
        consecutive_gains = PortfolioCalculatorService._get_max_consecutive(daily_changes, True)
        consecutive_losses = PortfolioCalculatorService._get_max_consecutive(daily_changes, False)

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
        """
        연속된 값의 최대 길이 계산

        Args:
            series: 부울 시리즈 (True/False)
            target_value: 찾을 값 (True 또는 False)

        Returns:
            연속된 값의 최대 길이
        """
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
                                              portfolio_results: Dict, total_amount: float) -> Tuple[Dict, Dict, list]:
        """
        개별 종목 백테스트의 실제 equity curve를 합산하여 포트폴리오 equity curve 계산
        (매수/매도 타이밍이 정확히 반영됨)

        Args:
            request: 포트폴리오 백테스트 요청
            portfolio_results: 각 종목의 백테스트 결과
            total_amount: 초기 투자금

        Returns:
            Tuple[equity_curve, daily_returns, weight_history]
        """
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
            return await self._fallback_equity_curve(request, portfolio_results, total_amount)

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

    async def _fallback_equity_curve(self, request: PortfolioBacktestRequest,
                              portfolio_results: Dict, total_amount: float) -> Tuple[Dict, Dict, list]:
        """
        데이터가 없을 때 사용하는 기본 equity curve (선형)

        Args:
            request: 포트폴리오 백테스트 요청
            portfolio_results: 각 종목의 백테스트 결과
            total_amount: 초기 투자금

        Returns:
            Tuple[equity_curve, daily_returns, weight_history]
        """
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


# 싱글톤 인스턴스
portfolio_calculator_service = PortfolioCalculatorService()
