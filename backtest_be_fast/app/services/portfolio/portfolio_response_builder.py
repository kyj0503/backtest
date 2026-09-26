"""포트폴리오 백테스트 응답 구성

PortfolioManagerService가 돌려주는 `{'status': 'success', 'data': {...}}` 딕셔너리를
경로별로 만든다. JSON 호환 변환(recursive_serialize)은 서비스가 성공 메트릭을
기록한 뒤 마지막에 한 번 한다.

키 이름과 순서가 곧 API 계약이다. 전략·buy&hold·현금 전용 경로의 `data` 키 목록과
순서는 서로 다르며(예: 현금 전용에는 individual_results가 없다) 기존 응답을 그대로
따른다 — tests/unit/test_portfolio_manager_response_snapshot.py가 고정한다.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.dca_calculator import DcaCalculator
from app.services.portfolio.portfolio_execution import StrategyRunOutcome
from app.services.portfolio.portfolio_statistics_builder import build_cash_only_statistics

logger = logging.getLogger(__name__)


def format_individual_results_list(
    individual_returns: Dict[str, Any],
    portfolio_results: Dict[str, Any] = None,
    mode: str = 'strategy'
) -> List[Dict[str, Any]]:
    """individual_returns를 테스트 호환 리스트로 변환합니다."""
    results = []
    for key, returns in individual_returns.items():
        if mode == 'strategy':
            results.append({
                'ticker': returns['symbol'],
                'final_equity': returns['final_value'],
                'total_return_pct': returns['return'],
                'sharpe_ratio': portfolio_results[key].get('strategy_stats', {}).get('sharpe_ratio', 0.0) if portfolio_results and key in portfolio_results else 0.0,
                'weight': returns['weight'],
                'amount': returns['amount'],
                'trades': returns.get('trades', 0),
                # 거래 기준 승률. 거래가 없으면 None (Trade_Win_Rate와 같은 규칙)
                'win_rate': returns.get('win_rate') if returns.get('trades') else None
            })
        else:  # buy_hold
            results.append({
                'ticker': returns['symbol'] if returns.get('symbol') else key,
                'final_equity': returns['amount'] + (returns['amount'] * returns['return'] / 100),
                'total_return_pct': returns['return'],
                'sharpe_ratio': 0.0,
                'weight': returns['weight'],
                'amount': returns['amount'],
                'trades': 1 if returns.get('symbol', '') != 'CASH' else 0,
                # buy&hold 포지션은 청산된 거래가 없어 거래 승률을 정의할 수 없다.
                # 과거에는 수익이면 100, 아니면 0을 지어냈다(A-09 부류)
                'win_rate': None
            })
    return results


def _cash_individual_return(weight: float, cash_amount: float) -> Dict[str, Any]:
    return {
        'weight': weight,
        'amount': cash_amount,
        'return': 0.0,  # 현금 수익률은 0%
        'start_price': 1.0,
        'end_price': 1.0,
        'investment_type': 'lump_sum',
        'asset_type': 'cash'  # 진짜 현금 자산임을 표시
    }


def _trade_log_entry(entry_time: str, price: float, shares: float, trade_type: str) -> Dict[str, Any]:
    return {
        'EntryTime': entry_time,
        'EntryPrice': float(price),
        'Size': float(shares),
        'Type': trade_type,
        'ExitTime': None,
        'ExitPrice': None,
        'PnL': None,
        'ReturnPct': None,
        'Duration': None,
    }


# ---------------------------------------------------------------------------
# 전략 경로
# ---------------------------------------------------------------------------

def strategy_failure_warnings(failed_symbols: List[Dict[str, str]]) -> List[str]:
    """실패 종목 경고 메시지 생성"""
    warnings = []
    if failed_symbols:
        for fs in failed_symbols:
            warnings.append(f"종목 {fs['symbol']} 백테스트 실패: {fs['error']}")
        logger.warning(f"실패한 종목 {len(failed_symbols)}개: {[fs['symbol'] for fs in failed_symbols]}")
    return warnings


def build_strategy_response(
    *,
    outcome: StrategyRunOutcome,
    portfolio_statistics: Dict[str, Any],
    portfolio_return: float,
    equity_curve: Dict[str, float],
    daily_returns: Dict[str, float],
    weight_history: List[Any],
) -> Dict[str, Any]:
    portfolio_results = outcome.portfolio_results
    individual_results_list = format_individual_results_list(
        outcome.individual_returns, portfolio_results, mode='strategy'
    )
    warnings = strategy_failure_warnings(outcome.failed_symbols)

    return {
        'status': 'success',
        'data': {
            'portfolio_statistics': portfolio_statistics,
            'individual_returns': outcome.individual_returns,
            'individual_results': individual_results_list,  # 테스트 호환성을 위한 리스트 형태
            'portfolio_result': {  # 테스트에서 기대하는 구조
                'total_equity': outcome.total_portfolio_value,
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
            'rebalance_history': [],  # 전략 포트폴리오는 리밸런싱 없음
            'warnings': warnings,
        }
    }


# ---------------------------------------------------------------------------
# 현금 전용 (buy&hold 경로에서 주식 데이터가 하나도 없을 때)
# ---------------------------------------------------------------------------

def build_cash_only_response(
    request: PortfolioBacktestRequest, cash_amount: float, warnings: List[str]
) -> Dict[str, Any]:
    start_date_obj = datetime.strptime(request.start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(request.end_date, '%Y-%m-%d')
    duration_days = (end_date_obj - start_date_obj).days
    statistics = build_cash_only_statistics(request, duration_days, cash_amount)

    individual_returns = {'CASH': _cash_individual_return(1.0, cash_amount)}

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

    return {
        'status': 'success',
        'data': {
            'portfolio_statistics': statistics,
            'individual_returns': individual_returns,
            'portfolio_composition': [
                {'symbol': 'CASH', 'weight': 1.0, 'amount': cash_amount, 'investment_type': 'lump_sum'}
            ],
            'equity_curve': equity_curve,
            'daily_returns': daily_returns,
            'warnings': warnings,
        }
    }


# ---------------------------------------------------------------------------
# buy&hold 시뮬레이션 경로
# ---------------------------------------------------------------------------

def build_buy_hold_individual_returns(
    amounts: Dict[str, float],
    dca_info: Dict[str, DcaStrategyInfo],
    portfolio_data: Dict[str, pd.DataFrame],
    cash_amount: float,
    total_amount: float,
    start_date: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """개별 종목 수익률(참고용, 현금 포함)과 종목별 거래 로그(strategy_details).

    현금은 여러 항목이어도 'CASH' 하나로 합쳐 맨 앞에 둔다. 일시불은 첫 가격
    대비 마지막 가격, DCA는 DcaCalculator의 평균 단가 기준 수익률이다.
    """
    individual_returns = {}
    strategy_details = {}  # 거래 로그를 저장할 딕셔너리

    if cash_amount > 0:
        individual_returns['CASH'] = _cash_individual_return(cash_amount / total_amount, cash_amount)

    # 주식 수익률 추가 (중복 종목 지원)
    for unique_key, amount in amounts.items():
        if unique_key.endswith('_CASH') or (unique_key in dca_info and dca_info[unique_key].asset_type == 'cash'):
            continue

        symbol = dca_info[unique_key].symbol
        if symbol not in portfolio_data:
            continue
        df = portfolio_data[symbol]
        if len(df) == 0:
            continue

        investment_type = dca_info[unique_key].investment_type
        weight = amount / total_amount

        if investment_type == 'lump_sum':
            # 일시불: 시작가 대비 종료가로 수익률 계산
            start_price = df['Close'].iloc[0]
            end_price = df['Close'].iloc[-1]
            individual_return = (end_price / start_price - 1) * 100

            # 일시불 매수 거래 로그 생성
            total_shares = amount / start_price
            trade_log = [_trade_log_entry(df.index[0].isoformat(), start_price, total_shares, 'BUY')]

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
        else:  # DCA
            # 분할매수: DcaCalculator를 사용하여 수익률 계산
            dca_periods = dca_info[unique_key].dca_periods
            period_amount = dca_info[unique_key].monthly_amount  # 회당 투자 금액
            dca_frequency = dca_info[unique_key].dca_frequency  # DCA 주기

            total_shares, average_price, individual_return, trade_log = DcaCalculator.calculate_dca_shares_and_return(
                df, period_amount, dca_periods, start_date, dca_frequency
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
            'trade_log': trade_log
        }

    return individual_returns, strategy_details


def append_rebalance_trades(
    strategy_details: Dict[str, Any],
    rebalance_history: List[Dict[str, Any]],
    dca_info: Dict[str, DcaStrategyInfo],
) -> None:
    """리밸런싱 거래(buy/sell)를 해당 종목의 trade_log 뒤에 붙인다 (현금은 제외)."""
    for rebalance_event in rebalance_history:
        rebalance_date = rebalance_event['date']
        for trade in rebalance_event['trades']:
            symbol = trade['symbol']
            action = trade['action']

            # unique_key 찾기 (symbol로 매칭)
            unique_key = None
            for key in dca_info.keys():
                if dca_info[key].symbol == symbol:
                    unique_key = key
                    break

            if unique_key and unique_key in strategy_details:
                # 거래 타입 결정 (buy/sell만 처리, 현금은 제외)
                if action in ['buy', 'sell']:
                    strategy_details[unique_key]['trade_log'].append(_trade_log_entry(
                        rebalance_date, trade['price'], trade['shares'],
                        'BUY' if action == 'buy' else 'SELL',
                    ))


def build_buy_hold_response(
    *,
    statistics: Dict[str, Any],
    individual_returns: Dict[str, Any],
    strategy_details: Dict[str, Any],
    amounts: Dict[str, float],
    dca_info: Dict[str, DcaStrategyInfo],
    total_amount: float,
    portfolio_result: pd.DataFrame,
    warnings: List[str],
) -> Dict[str, Any]:
    individual_results_list = format_individual_results_list(
        individual_returns, mode='buy_hold'
    )

    # 리밸런싱 히스토리와 비중 변화 데이터 추출
    rebalance_history = portfolio_result.attrs.get('rebalance_history', [])
    weight_history = portfolio_result.attrs.get('weight_history', [])

    append_rebalance_trades(strategy_details, rebalance_history, dca_info)

    return {
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
                    'symbol': dca_info[unique_key].symbol,  # 실제 symbol 사용 (프론트엔드 호환)
                    'weight': amount / total_amount,
                    'amount': amount,
                    'investment_type': dca_info[unique_key].investment_type,
                    'dca_periods': dca_info[unique_key].dca_periods if dca_info[unique_key].investment_type == 'dca' else None,
                    'asset_type': dca_info[unique_key].asset_type
                }
                for unique_key, amount in amounts.items()
            ],
            'equity_curve': {
                date.strftime('%Y-%m-%d'): value * total_amount
                for date, value in portfolio_result['Portfolio_Value'].items()
            },
            # 수익률은 API 응답에서 백분율(2.5 = 2.5%)이다. 시뮬레이션 결과의
            # Daily_Return은 소수(0.025)이므로 여기서 한 번만 100을 곱한다. 이미
            # 백분율이므로 FE는 표시할 때 그대로 쓰고, 복리 계산처럼 소수가 필요할
            # 때만 /100으로 되돌린다(예: BenchmarkIndexChart). 이중 변환 금지.
            'daily_returns': {
                date.strftime('%Y-%m-%d'): return_val * 100  # 소수 → 백분율 변환 (0.025 → 2.5)
                for date, return_val in portfolio_result['Daily_Return'].items()
            },
            'strategy_details': strategy_details,  # 거래 로그 포함
            'rebalance_history': rebalance_history,
            'weight_history': weight_history,
            # 전략 경로와 같은 계약 — FE는 'warnings' 키로 배너를 띄운다
            'warnings': warnings,
        }
    }
