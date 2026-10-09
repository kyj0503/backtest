"""포트폴리오 백테스트 실행 단계

PortfolioManagerService의 두 경로가 입력 변환 뒤에 실제 계산을 돌리는 부분이다.

- 전략 경로: 종목마다 backtest_service로 같은 전략을 돌려 결과를 모은다.
- buy&hold 경로: 통화·환율을 준비해 PortfolioSimulationEngine에 일별 시뮬레이션을 맡긴다.

통계 조립과 응답 구성은 portfolio_statistics_builder / portfolio_response_builder 몫이다.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from app.domain.portfolio_domain import DcaStrategyInfo
from app.schemas.requests import BacktestRequest
from app.schemas.schemas import PortfolioBacktestRequest
from app.services.backtest_service import backtest_service
from app.services.portfolio.portfolio_inputs import strategy_asset_key

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 전략 경로
# ---------------------------------------------------------------------------

@dataclass
class StrategyRunOutcome:
    """종목별 전략 백테스트 결과 모음.

    portfolio_results: symbol → 금액·비중·strategy_stats(개별 백테스트 결과 dict)
    individual_returns: symbol → 응답용 종목 수익률
    total_portfolio_value: 성공 종목 최종 평가금 + 현금 합계
    failed_symbols: [{'symbol', 'error'}] — 예외로 실패한 종목
    """
    portfolio_results: Dict[str, Any] = field(default_factory=dict)
    individual_returns: Dict[str, Any] = field(default_factory=dict)
    total_portfolio_value: float = 0
    failed_symbols: List[Dict[str, str]] = field(default_factory=list)


def _cash_result(outcome: StrategyRunOutcome, key: str, symbol: str, amount: float, weight: float) -> None:
    """현금 처리 (수익률 0%, 전략 적용 안함)"""
    logger.info(f"현금 자산 {symbol} 처리 (투자금액: ${amount:,.2f}, 비중: {weight:.3f})")

    outcome.portfolio_results[key] = {
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

    outcome.individual_returns[key] = {
        'symbol': symbol,
        'weight': weight,
        'amount': amount,
        'return': 0.0,
        'initial_value': amount,
        'final_value': amount,
        'trades': 0,
        'win_rate': None  # 거래가 없으면 거래 승률은 계산 불가
    }

    outcome.total_portfolio_value += amount
    logger.info(f"현금 자산 완료: 0.00% 수익률")


async def run_strategy_per_symbol(
    request: PortfolioBacktestRequest,
    amounts: Dict[str, float],
    total_amount: float,
    strategy_name: str,
) -> StrategyRunOutcome:
    """각 종목에 같은 전략을 적용해 개별 백테스트를 실행한다.

    예외 또는 평가금 누락으로 실패한 종목은 failed_symbols에 기록한다.
    """
    outcome = StrategyRunOutcome()

    for idx, item in enumerate(request.portfolio):
        symbol = item.symbol
        # amount/weight 동시 지원
        key = strategy_asset_key(item, idx, request.portfolio)
        amount = amounts[key]
        weight = amount / total_amount if total_amount > 0 else 0.0

        if item.asset_type == 'cash':
            _cash_result(outcome, key, symbol, amount, weight)
            continue

        logger.info(f"종목 {symbol} (#{idx+1}) 전략 백테스트 실행 (투자금액: ${amount:,.2f}, 비중: {weight:.3f})")

        # 개별 종목 백테스트 요청 생성
        backtest_req = BacktestRequest(
            ticker=symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_cash=amount,
            strategy=strategy_name,
            strategy_params=request.strategy_params or {},
            commission=request.commission
        )

        try:
            # 개별 종목 백테스트 실행
            result = await backtest_service.run_backtest(backtest_req)

            if result and hasattr(result, 'final_equity'):
                final_value = result.final_equity
                initial_value = amount
                stock_return = (final_value / initial_value - 1) * 100

                outcome.portfolio_results[symbol] = {
                    'symbol': symbol,
                    'initial_value': initial_value,
                    'final_value': final_value,
                    'return_pct': stock_return,
                    'weight': weight,
                    'amount': amount,
                    'strategy_stats': result.__dict__  # 객체를 딕셔너리로 변환
                }

                outcome.individual_returns[symbol] = {
                    'symbol': symbol,
                    'weight': weight,
                    'amount': amount,
                    'return': stock_return,
                    'initial_value': initial_value,
                    'final_value': final_value,
                    'trades': getattr(result, 'total_trades', 0),
                    # backtesting.py는 거래가 없으면 승률을 NaN으로 주고 엔진이
                    # 0.0으로 바꾼다. 0%(전부 패배)와 구분되도록 None으로 둔다
                    'win_rate': (
                        getattr(result, 'win_rate_pct', None)
                        if getattr(result, 'total_trades', 0) else None
                    )
                }

                outcome.total_portfolio_value += final_value

                logger.info(f"종목 {symbol} (#{idx+1}) 완료: {stock_return:.2f}% 수익률, 거래수: {getattr(result, 'total_trades', 0)}")
            else:
                logger.warning(f"종목 {symbol} 백테스트 실패: 결과가 없거나 final_equity 속성이 없음")
                outcome.failed_symbols.append({'symbol': symbol, 'error': '백테스트 평가금 누락'})

        except Exception as e:
            logger.error(f"종목 {symbol} 백테스트 오류: {str(e)}")
            outcome.failed_symbols.append({'symbol': symbol, 'error': str(e)})
            continue

    return outcome


# ---------------------------------------------------------------------------
# buy&hold 경로
# ---------------------------------------------------------------------------

async def simulate_buy_hold(
    data_loader,
    simulation_engine,
    portfolio_data: Dict[str, pd.DataFrame],
    amounts: Dict[str, float],
    dca_info: Dict[str, DcaStrategyInfo],
    start_date: str,
    end_date: str,
    rebalance_frequency: str,
    commission: float,
) -> pd.DataFrame:
    """DCA와 리밸런싱을 고려한 포트폴리오 일별 시뮬레이션.

    data_loader·simulation_engine은 호출 시점의 서비스 인스턴스 속성을 받는다
    (테스트가 service.data_loader를 patch.object로 바꾼다).

    Note: last_rebalance_date는 예정일 추적용, rebalance_history는 실제 거래만 기록
    """
    # 현금 처리
    cash_amount = 0
    for unique_key, amount in amounts.items():
        if unique_key in dca_info and dca_info[unique_key].asset_type == 'cash':
            cash_amount += amount

    stock_amounts = {k: v for k, v in amounts.items() if k in dca_info and dca_info[k].asset_type != 'cash'}

    # 날짜 범위 설정
    all_dates = set()
    for unique_key, df in portfolio_data.items():
        if unique_key in dca_info and dca_info[unique_key].asset_type != 'cash':
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

    # 각 종목의 currency 정보 및 환율 로드 (Data Loader 위임)
    symbols = [dca_info[unique_key].symbol for unique_key in stock_amounts.keys()]

    # 1. Ticker Currencies 로드
    ticker_currencies = await data_loader.load_ticker_currencies(symbols)

    # unique_key에 맵핑
    keyed_ticker_currencies = {}
    for unique_key in stock_amounts.keys():
        symbol = dca_info[unique_key].symbol
        keyed_ticker_currencies[unique_key] = ticker_currencies.get(symbol, 'USD')

    # 2. Exchange Rates 로드
    required_currencies = list(set(keyed_ticker_currencies.values()) - {'USD'})

    exchange_rates_by_currency = await data_loader.load_exchange_rates(
        currencies=required_currencies,
        start_date=start_date,
        end_date=end_date,
        date_range=date_range
    )

    # 포트폴리오 시뮬레이션 실행 (목표 비중은 엔진이 amounts에서 직접 계산한다)
    return await simulation_engine.execute_simulation(
        date_range=date_range,
        start_date_obj=start_date_obj,
        end_date_obj=end_date_obj,
        stock_amounts=stock_amounts,
        amounts=amounts,
        cash_amount=cash_amount,
        total_amount=total_amount,
        portfolio_data=portfolio_data,
        dca_info=dca_info,
        ticker_currencies=ticker_currencies,
        exchange_rates_by_currency=exchange_rates_by_currency,
        rebalance_frequency=rebalance_frequency,
        commission=commission
    )
