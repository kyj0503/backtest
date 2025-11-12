# Quick Reference: Logging Gaps - Critical Operations

## CRITICAL Priority (Implement Immediately)

### 1. **backtest_engine.py:191-224** - Currency Conversion
- **Missing**: Which currency being converted, exchange rates used, conversion results
- **Impact**: Cannot audit currency conversion accuracy
- **Fix**: Log ticker currency detection, rate values, price range before/after conversion

### 2. **portfolio_service.py:158-167** - Exchange Rate Loading
- **Missing**: Which currencies are loaded, actual rate values, load status
- **Impact**: Cannot verify exchange rates used in multi-currency portfolios
- **Fix**: Log required currencies list, rate values range per currency, load success/failure

---

## HIGH Priority (Implement Soon)

### 3. **backtest_engine.py:226-263** - Strategy Parameter Override
- **Missing**: Which parameters were overridden and their final values
- **Impact**: Users cannot verify if strategy params were applied correctly
- **Fix**: Log overridden parameters and their values before execution

### 4. **portfolio_service.py:379-387** - Rebalancing Trigger Check
- **Missing**: Why rebalancing was/wasn't triggered on specific dates
- **Impact**: Users cannot verify rebalancing schedule execution
- **Fix**: Log trigger decision and reasons (frequency, asset count, date comparison)

### 5. **portfolio_service.py:438-595** - Rebalancing Trade Execution
- **Missing**: Individual buy/sell trades, commission details, weight adjustments
- **Impact**: No visibility into rebalancing operations at trade level
- **Fix**: Log each buy/sell trade, commission costs, before/after weights

### 6. **portfolio_service.py:215-248** - Currency Conversion (Daily Loop)
- **Missing**: Exchange rate source (current vs cached fallback), conversion summary
- **Impact**: Cannot identify dates with missing rate data
- **Fix**: Log rate source, add daily conversion summary

---

## MEDIUM Priority (Implement When Convenient)

### 7. **backtest_engine.py:402-428** - Benchmark Alpha/Beta Calculation
- **Missing**: Benchmark data load status, calculation process, results
- **Impact**: Silent failures make results unreliable
- **Fix**: Log benchmark load success, correlation calculations, final alpha/beta values

### 8. **portfolio_service.py:250-283** - Delisting Detection
- **Missing**: Price age/staleness summary, delisted stock count at rebalancing
- **Impact**: Users may not know which stocks became delisted
- **Fix**: Log price staleness, delisted count summary at rebalancing time

---

## LOW Priority (Enhanced Logging)

### 9-11. **DCA Execution & Rebalancing Weight Adjustment**
- Current: ✅ Good basic logging
- Enhancement: Add details on decision points, calculation details
- Impact: Nice-to-have for debugging edge cases

---

## Implementation Strategy

1. **Phase 1 (CRITICAL)**: Fix #1, #2 - Currency operations
2. **Phase 2 (HIGH)**: Fix #3, #4, #5, #6 - Strategy and rebalancing
3. **Phase 3 (MEDIUM)**: Fix #7, #8 - Benchmark and delisting
4. **Phase 4 (LOW)**: Enhance #9-11 - DCA details

---

## Testing Recommendations

After implementing logging:

1. **Run multi-currency backtest** → Verify exchange rates logged correctly
2. **Run rebalancing backtest** → Verify all rebalancing trades logged
3. **Run with benchmark ticker** → Verify alpha/beta calculation logged
4. **Run long-term DCA** → Verify delisting detection logged
5. **Check log output** → Search for "ERROR", "WARNING" level messages

---

## Files to Modify

- `/home/user/backtest/backtest_be_fast/app/services/backtest_engine.py`
- `/home/user/backtest/backtest_be_fast/app/services/portfolio_service.py`
- `/home/user/backtest/backtest_be_fast/app/utils/currency_converter.py` (optional enhancements)

---

## Example Commands for Testing

```bash
# View logs during backtest
docker compose -f compose.dev.yaml logs -f backtest-be-fast

# Search for specific operations
grep -i "통화 변환\|환율\|리밸런싱\|분할 매수" <log_file>

# Check for missing exchange rate warnings
grep "환율 없음\|환율 데이터 없음" <log_file>
```

