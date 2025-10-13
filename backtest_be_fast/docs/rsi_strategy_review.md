# RSI Strategy Implementation Review

## Summary
- The RSI-based mean-reversion strategy in `app/strategies/rsi_strategy.py` behaves as designed: it enters long positions when RSI drops below the oversold threshold and exits once RSI exceeds the overbought threshold.
- The RSI indicator leverages exponential moving averages for gain/loss smoothing, which improves stability and keeps calculations robust against divide-by-zero scenarios.
- Position sizing, entry, and exit logic are straightforward and guard against over-allocation by capping exposure at 95% of equity.

## Logic Assessment
### Indicator Initialization
- `self.I(self._rsi, close, self.rsi_period)` wires the RSI indicator into the backtesting engine so it updates with each new bar.
- `_rsi` applies exponential moving averages to the separated gains and losses, replaces zero losses with `np.finfo(float).eps`, and fills initial NaNs with 50 to ensure the indicator is usable from the first actionable bar.

### Trading Rules
- Entry: when RSI < oversold and no position is open, the strategy buys 95% of equity at the current close. The share count is floored to an integer to avoid fractional quantities.
- Exit: when RSI > overbought and a long position exists, the strategy closes the position. The logic intentionally remains long-only, matching the documented "oversold → buy, overbought → sell" specification.
- The `len(self.rsi) > self.rsi_period` guard prevents premature signals before the indicator is fully warmed up.

### Risk and Edge Cases
- The residual 5% cash buffer helps cover commissions or slippage if those are enabled during backtests.
- RSI smoothness can lead to whipsaws; adding secondary confirmation filters or cooldowns would be a domain-level enhancement rather than a fix.
- The strategy currently assumes long-only behavior; extending to short entries on overbought would be an optional enhancement if contrarian short exposure is desired.

## Recommendations
1. **Optional Short Exposure**: Add a configurable shorting branch on overbought signals if two-sided exposure becomes a requirement.
2. **Configurable Position Sizing**: Promote `position_size` to a tunable parameter so capital allocation can be controlled externally per backtest.
3. **Risk Controls**: Consider optional stop-loss / take-profit hooks for tighter risk management in more volatile datasets.

## Testing Notes
- Unit coverage exists in `tests/unit/test_rsi_strategy.py` and it exercises RSI computation, signal generation, and edge conditions. Attempted to run the test module locally, but the default environment lacks the required `poetry` executable; no code changes were needed for the review.
