import pandas as pd
from types import SimpleNamespace

from app.services.backtest.chart_data_service import chart_data_service
from app.services.backtest.backtest_engine import BacktestEngine
from app.models.requests import BacktestRequest, StrategyType


def _sample_price_frame():
    index = pd.date_range('2024-01-01', periods=5, freq='D')
    return pd.DataFrame(
        {
            'Open': [100, 101, 102, 103, 104],
            'High': [101, 102, 103, 104, 105],
            'Low': [99, 100, 101, 102, 103],
            'Close': [100, 102, 101, 103, 105],
            'Volume': [1000, 1200, 1100, 1500, 1300],
        },
        index=index,
    )


def test_trade_markers_generated_from_trade_log():
    data = _sample_price_frame()
    trade_log = [
        {
            'EntryTime': pd.Timestamp('2024-01-02'),
            'ExitTime': pd.Timestamp('2024-01-04'),
            'EntryPrice': 102.0,
            'ExitPrice': 103.0,
            'Direction': 'Long',
            'Size': 1.5,
            'PnL (%)': 1.2,
        }
    ]

    markers = chart_data_service._generate_trade_markers(data, 'sma_crossover', trade_log)

    assert len(markers) == 2
    entry = next(m for m in markers if m.type == 'entry')
    exit_trade = next(m for m in markers if m.type == 'exit')

    assert entry.side == 'buy'
    assert exit_trade.side == 'sell'
    assert abs(entry.price - 102.0) < 1e-6
    assert abs(exit_trade.price - 103.0) < 1e-6
    assert exit_trade.pnl_pct == 1.2


def test_rsi_indicator_generation_returns_lines():
    data = _sample_price_frame()
    indicators = chart_data_service._generate_rsi_indicators(
        data,
        {
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
        },
    )

    names = {indicator.name for indicator in indicators}
    assert 'RSI_14' in names
    assert 'RSI_OVERBOUGHT' in names
    assert 'RSI_OVERSOLD' in names


def test_convert_result_to_response_includes_alpha_beta_and_trade_log(monkeypatch):
    engine = BacktestEngine()

    stats = pd.Series(
        {
            'Equity Final [$]': 10300.0,
            'Return [%]': 3.0,
            'Return (Ann.) [%]': 3.0,
            'Buy & Hold Return [%]': 2.5,
            'Volatility [%]': 10.0,
            'Sharpe Ratio': 1.0,
            'Sortino Ratio': 1.2,
            'Calmar Ratio': 0.8,
            'Max. Drawdown [%]': -5.0,
            'Avg. Drawdown [%]': -2.0,
            '# Trades': 1,
            'Win Rate [%]': 100.0,
            'Profit Factor': 2.0,
            'Avg. Trade [%]': 3.0,
            'Best Trade [%]': 3.0,
            'Worst Trade [%]': 0.0,
            'SQN': 1.5,
            '_trades': pd.DataFrame([
                {
                    'EntryTime': pd.Timestamp('2024-01-02'),
                    'ExitTime': pd.Timestamp('2024-01-03'),
                    'EntryPrice': 100.0,
                    'ExitPrice': 103.0,
                    'Direction': 'Long',
                    'Size': 1.0,
                    'PnL (%)': 3.0,
                }
            ]),
            '_equity_curve': pd.DataFrame(
                {
                    'Equity': [10000.0, 10100.0, 10050.0, 10300.0],
                },
                index=pd.date_range('2024-01-01', periods=4, freq='D'),
            ),
        }
    )

    benchmark_prices = pd.DataFrame(
        {
            'Close': [100, 101, 100.5, 102],
        },
        index=pd.date_range('2024-01-01', periods=4, freq='D'),
    )

    monkeypatch.setattr(
        engine,
        'data_fetcher',
        SimpleNamespace(get_stock_data=lambda ticker, start_date, end_date: benchmark_prices),
    )

    request = BacktestRequest(
        ticker='AAPL',
        start_date='2024-01-01',
        end_date='2024-01-04',
        initial_cash=10000.0,
        strategy=StrategyType.SMA_CROSSOVER,
        strategy_params={},
        commission=0.0,
        spread=0.0,
        benchmark_ticker='SPY',
    )

    result = engine._convert_result_to_response(stats, request)

    assert result.alpha_pct is not None
    assert result.beta is not None
    assert len(result.trade_log) == 1
