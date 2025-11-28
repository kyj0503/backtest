"""포트폴리오 지표 계산

일일 포트폴리오 메트릭 및 통계를 계산합니다 (수익률, 샤프 비율, 최대 낙폭 등).
"""

import logging
from typing import Dict, Any, Tuple
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class PortfolioMetrics:
    """포트폴리오 지표 계산 클래스"""

    @staticmethod
    def calculate_daily_metrics_and_history(
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

    @staticmethod
    def calculate_portfolio_statistics(
        portfolio_returns: pd.DataFrame,
        total_amount: float
    ) -> Dict[str, Any]:
        """
        포트폴리오 통계를 계산합니다.

        **계산 항목**:
        - 총수익률, 연간수익률
        - 최대 낙폭, 평균 낙폭
        - 연간 변동성, 샤프 비율
        - 연속 상승/하락일
        - 수익 인수(Profit Factor), 승률

        Args:
            portfolio_returns: Portfolio_Value, Daily_Return 컬럼을 포함한 DataFrame
            total_amount: 초기 투자금

        Returns:
            통계 정보 딕셔너리
        """
        import numpy as np

        start_date = portfolio_returns.index[0]
        end_date = portfolio_returns.index[-1]
        duration = (end_date - start_date).days

        final_value = portfolio_returns['Portfolio_Value'].iloc[-1]
        peak_value = portfolio_returns['Portfolio_Value'].max()

        total_return = (final_value - 1) * 100

        # 드로우다운 계산
        running_max = portfolio_returns['Portfolio_Value'].expanding().max()
        drawdown = (portfolio_returns['Portfolio_Value'] - running_max) / running_max * 100
        max_drawdown = drawdown.min()
        avg_drawdown = drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else 0

        # 변동성 및 샤프 비율
        daily_returns = portfolio_returns['Daily_Return']
        annual_volatility = daily_returns.std() * np.sqrt(252) * 100
        annual_return = ((final_value ** (365.25 / duration)) - 1) * 100 if duration > 0 else 0

        # 무위험 수익률을 0으로 가정한 샤프 비율
        sharpe_ratio = (annual_return / annual_volatility) if annual_volatility > 0 else 0

        # 최대 연속 상승/하락일
        daily_changes = daily_returns > 0
        consecutive_gains = PortfolioMetrics._get_max_consecutive(daily_changes, True)
        consecutive_losses = PortfolioMetrics._get_max_consecutive(daily_changes, False)

        # Profit Factor 계산
        positive_returns = daily_returns[daily_returns > 0]
        negative_returns = daily_returns[daily_returns < 0]

        gross_profit = positive_returns.sum() if len(positive_returns) > 0 else 0
        gross_loss = abs(negative_returns.sum()) if len(negative_returns) > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (2.0 if gross_profit > 0 else 1.0)

        # 실제 거래 횟수 추출
        total_trades = portfolio_returns.attrs.get('total_trades', 0)

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
            'Total_Trading_Days': len(portfolio_returns),
            'Total_Trades': total_trades,
            'Positive_Days': len(daily_returns[daily_returns > 0]),
            'Negative_Days': len(daily_returns[daily_returns < 0]),
            'Win_Rate': len(daily_returns[daily_returns > 0]) / len(daily_returns) * 100 if len(daily_returns) > 0 else 0,
            'Profit_Factor': profit_factor
        }

    @staticmethod
    def _get_max_consecutive(series: pd.Series, target_value: bool) -> int:
        """
        연속된 요소의 최대 개수를 구합니다.

        Args:
            series: 부울 시리즈
            target_value: 찾을 값 (True 또는 False)

        Returns:
            최대 연속 개수
        """
        if len(series) == 0:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for value in series:
            if value == target_value:
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive
