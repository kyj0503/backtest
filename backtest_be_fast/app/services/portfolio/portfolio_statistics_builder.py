"""포트폴리오 통계 조립 (portfolio_statistics 딕셔너리)

PortfolioManagerService의 전략 경로와 현금 전용 경로가 응답의
`portfolio_statistics`를 만드는 규칙이다. buy&hold 시뮬레이션 경로는
portfolio_calculator.calculate_portfolio_statistics()의 결과를 그대로 쓴다.

키 이름과 순서는 FE 계약이다(A-09에서 경로 간 정의를 통일). 여기서 순서를
바꾸면 응답 JSON의 키 순서가 바뀐다.
"""
from datetime import datetime
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_calculator_service import portfolio_calculator


def calculate_weighted_stats(portfolio_results: Dict[str, Any]) -> Dict[str, float]:
    """포트폴리오 결과에서 종목별 전략 통계를 합산·가중평균합니다.

    `trade_win_rate`는 전 종목의 거래를 합친 거래 기준 승률(%)이다 —
    종목별 승률을 거래 수로 가중평균하면 "이긴 거래 수 / 전체 거래 수"와 같다.
    과거에는 투자금 비중으로 가중평균해 거래가 없는 현금 비중만큼 승률이
    깎였다(현금 50% → 승률 절반). 거래가 하나도 없으면 None.
    """
    total_trades = sum(
        r.get('strategy_stats', {}).get('total_trades', 0)
        for r in portfolio_results.values()
    )
    winning_trades = 0.0
    for r in portfolio_results.values():
        stats = r.get('strategy_stats', {})
        trades = stats.get('total_trades', 0) or 0
        win_rate = stats.get('win_rate_pct', 0) or 0
        if trades > 0 and np.isfinite(win_rate):
            winning_trades += trades * win_rate / 100
    trade_win_rate = winning_trades / total_trades * 100 if total_trades > 0 else None
    weighted_max_drawdown = sum(
        r['weight'] * abs(r.get('strategy_stats', {}).get('max_drawdown_pct', 0))
        for r in portfolio_results.values()
    )
    weighted_sharpe_ratio = sum(
        r['weight'] * r.get('strategy_stats', {}).get('sharpe_ratio', 0)
        for r in portfolio_results.values()
    )
    return {
        'total_trades': total_trades,
        'trade_win_rate': trade_win_rate,
        'weighted_max_drawdown': weighted_max_drawdown,
        'weighted_sharpe_ratio': weighted_sharpe_ratio,
    }


def calculate_true_portfolio_stats(
    equity_curve: Dict[str, float],
    daily_returns: Dict[str, float],
    total_amount: float
) -> Dict[str, Any]:
    """집계된 포트폴리오 equity curve에서 실제 포트폴리오 지표를 계산합니다 (P2-08).

    개별 종목 지표의 가중평균(예: Sharpe, MDD)은 종목 간 상관관계와 하락 시점의
    차이를 무시하므로 포트폴리오 전체의 진짜 지표가 아니다. 예를 들어 두 종목이
    서로 다른 날짜에 하락하면 포트폴리오 MDD는 각 종목 MDD의 가중평균보다
    완만해야 하는데, 가중평균 방식은 이를 반영하지 못한다.

    buy&hold 경로가 이미 같은 목적으로 사용하는
    portfolio_calculator.calculate_portfolio_statistics()를 그대로 재사용해
    두 경로의 지표 산출 방식을 일치시킨다.

    Args:
        equity_curve: 날짜별 포트폴리오 총 가치(달러). 이미 종목별 실제
            equity curve를 합산해 만들어진 값
            (_calculate_realistic_equity_curve의 결과)
        daily_returns: 날짜별 포트폴리오 일간 수익률(퍼센트 단위, 예: 2.5 = 2.5%)
        total_amount: 초기 총 투자금 (정규화 기준)

    Returns:
        portfolio_calculator.calculate_portfolio_statistics()와 동일한 키를 가진
        딕셔너리 (Sharpe_Ratio, Max_Drawdown, Avg_Drawdown, Peak_Value,
        Total_Trading_Days 등 포함)
    """
    dates_sorted = sorted(equity_curve.keys())
    equity_df = pd.DataFrame(
        {
            'Portfolio_Value': [equity_curve[d] / total_amount for d in dates_sorted],
            'Daily_Return': [daily_returns.get(d, 0.0) / 100.0 for d in dates_sorted],
        },
        index=pd.to_datetime(dates_sorted)
    )
    return portfolio_calculator.calculate_portfolio_statistics(equity_df, total_amount)


def duration_days_of(request: PortfolioBacktestRequest) -> int:
    """요청 기간의 달력 일수 (end - start)."""
    start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
    return (end_date_obj - start_date_obj).days


def strategy_headline_returns(
    request: PortfolioBacktestRequest,
    total_amount: float,
    total_portfolio_value: float,
) -> Tuple[float, int, float]:
    """전략 경로의 (총 수익률 %, 기간 일수, 연환산 수익률 %).

    전략 경로는 중도 납입이 없어(A-02: DCA 거부) 최종/원금 연환산이 곧
    시간가중(TWR) 연환산과 같은 정의다 (A-19).
    """
    portfolio_return = (total_portfolio_value / total_amount - 1) * 100
    duration_days = duration_days_of(request)
    annual_return = ((total_portfolio_value / total_amount) ** (365.25 / duration_days) - 1) * 100 if duration_days > 0 else 0
    return portfolio_return, duration_days, annual_return


def build_strategy_statistics(
    request: PortfolioBacktestRequest,
    *,
    duration_days: int,
    total_amount: float,
    total_portfolio_value: float,
    portfolio_return: float,
    annual_return: float,
    weighted_stats: Dict[str, Any],
    true_portfolio_stats: Dict[str, Any],
) -> Dict[str, Any]:
    """전략 경로의 portfolio_statistics (프론트엔드 호환).

    일 기준 지표(변동성·상승/하락일·연속일·Win_Rate·Profit_Factor)는 집계
    equity curve에서 계산한 true_portfolio_stats를 써서 buy&hold 경로와 같은
    정의를 따른다 (A-09). 거래 수와 거래 기준 승률만 종목별 합산값이다.
    """
    return {
        'Start': request.start_date,
        'End': request.end_date,
        'Duration': f'{duration_days} days',
        'Initial_Value': total_amount,
        'Final_Value': total_portfolio_value,
        'Peak_Value': true_portfolio_stats['Peak_Value'],
        'Total_Return': portfolio_return,
        'Annual_Return': annual_return,
        'Annual_Volatility': true_portfolio_stats['Annual_Volatility'],
        'Sharpe_Ratio': true_portfolio_stats['Sharpe_Ratio'],
        'Max_Drawdown': true_portfolio_stats['Max_Drawdown'],
        'Avg_Drawdown': true_portfolio_stats['Avg_Drawdown'],
        'Max_Consecutive_Gains': true_portfolio_stats['Max_Consecutive_Gains'],
        'Max_Consecutive_Losses': true_portfolio_stats['Max_Consecutive_Losses'],
        'Total_Trading_Days': true_portfolio_stats['Total_Trading_Days'],
        'Total_Trades': weighted_stats['total_trades'],
        'Positive_Days': true_portfolio_stats['Positive_Days'],
        'Negative_Days': true_portfolio_stats['Negative_Days'],
        'Win_Rate': true_portfolio_stats['Win_Rate'],
        # 거래 기준 승률(전 종목 거래 합산). 전략 경로에만 있다.
        'Trade_Win_Rate': weighted_stats['trade_win_rate'],
        'Profit_Factor': true_portfolio_stats['Profit_Factor'],
    }


def build_cash_only_statistics(
    request: PortfolioBacktestRequest, duration_days: int, cash_amount: float
) -> Dict[str, Any]:
    """현금만 있는 포트폴리오의 portfolio_statistics (현금은 수익률 0%)."""
    return {
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
        'Win_Rate': 0.0,
        # 손실일이 없으니 정의되지 않는다 — 다른 경로와 같은 계약 (A-09)
        'Profit_Factor': None,
    }
