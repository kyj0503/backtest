# Critical Operations Lacking Logging - Analysis Report

## Executive Summary
Identified **11 critical operations** across both files that lack comprehensive logging for debugging and monitoring. These operations are essential for troubleshooting backtest accuracy issues, especially around currency conversions, DCA execution, and rebalancing.

---

## FILE 1: backtest_engine.py

### 1. Currency Conversion Operation (Lines 191-224)

**Location**: `_convert_to_usd()` method

**Operation Description**: 
- Converts non-USD currency price data to USD using exchange rates
- Wrapper method that calls `currency_converter.convert_dataframe_to_usd()`
- Critical for backtest calculation accuracy

**Current Logging**:
- ❌ NO logging - Method is completely silent on what currencies are converted, which exchange rates are used, or conversion results

**Suggested Logging Statements**:
```python
# At start of method (after ticker currency detection):
logger.info(f"통화 변환 시작: {ticker}, 데이터 범위 {len(data)} 행, 기간: {start_date} ~ {end_date}")

# Before calling converter:
ticker_currency = SUPPORTED_CURRENCIES.get(ticker, 'USD')
if ticker_currency != 'USD':
    logger.info(f"비USD 통화 감지: {ticker} = {ticker_currency}, USD로 변환 필요")

# After conversion (inside currency_converter wrapper):
logger.debug(f"가격 변환 범위: {data['Close'].min():.2f} ~ {data['Close'].max():.2f} {ticker_currency} "
             f"→ ${converted_data['Close'].min():.2f} ~ ${converted_data['Close'].max():.2f}")
logger.info(f"통화 변환 완료: {ticker} ({ticker_currency} → USD)")
```

**Why It Matters**:
- Exchange rates are critical for backtest accuracy
- Race condition or incorrect rate loading can silently corrupt results
- No way to verify which rates were actually used without code inspection

---

### 2. Strategy Parameter Override (Lines 226-263)

**Location**: `_build_strategy()` method, lines 259-263

**Operation Description**:
- Builds custom strategy class with user-provided parameter overrides
- Creates dynamic strategy subclass with overridden attributes

**Current Logging**:
- ⚠️ PARTIAL - Logs warning on validation failure (line 246-250)
- ❌ Missing: No logging of successfully applied parameter overrides
- ❌ Missing: No logging of final parameter values used

**Suggested Logging Statements**:
```python
# After sanitized_params validation (around line 240):
if sanitized_params:
    logger.debug(f"전략 파라미터 검증 성공: {sanitized_params}")

# Before building overrides (around line 253):
if overrides:
    logger.info(f"전략 파라미터 오버라이드: {strategy_name}")
    for key, value in overrides.items():
        logger.debug(f"  {key}: {value}")
    logger.info(f"커스텀 전략 생성: {configured_name}")
else:
    logger.debug(f"전략 파라미터 오버라이드 없음, 기본 전략 사용: {strategy_name}")
```

**Why It Matters**:
- Users may be confused if parameters aren't applied as expected
- Helps verify strategy parameters in logs for reproducibility

---

### 3. Benchmark Alpha/Beta Calculation (Lines 402-428)

**Location**: `_convert_result_to_response()` method, benchmark calculation section

**Operation Description**:
- Calculates alpha and beta against a benchmark ticker
- Correlates strategy returns with benchmark returns
- Optional feature but affects result interpretation

**Current Logging**:
- ❌ NO logging - Entire benchmark calculation is silent
- Line 404: Fetches benchmark data with no logging
- Lines 416-426: Performs calculations with no logging
- Line 427: Silent pass on exception

**Suggested Logging Statements**:
```python
# At start of benchmark calculation (after line 402):
if getattr(request, 'benchmark_ticker', None):
    logger.info(f"벤치마크 분석 시작: {request.benchmark_ticker}")

# After fetching benchmark (after line 408):
    if benchmark is not None and not benchmark.empty:
        logger.info(f"벤치마크 데이터 로드 완료: {len(benchmark)} 행")
        logger.debug(f"벤치마크 가격 범위: ${benchmark['Close'].min():.2f} ~ ${benchmark['Close'].max():.2f}")
    else:
        logger.warning(f"벤치마크 {request.benchmark_ticker} 데이터 없음, 알파/베타 계산 스킵")

# After calculating correlations (after line 416):
    if len(strat_returns) > 1 and bench_returns.var() != 0:
        logger.debug(f"수익률 상관관계 계산: 전략 {len(strat_returns)}개 기간, 벤치마크 {len(bench_returns)}개 기간")

# After calculating alpha/beta (after line 426):
        logger.info(f"알파/베타 계산 완료: α={alpha_pct:.2f}%, β={beta_value:.4f}")
        logger.debug(f"공분산={cov:.6f}, 벤치마크 분산={var_bench:.6f}")

# On exception (line 427):
    except Exception as e:
        logger.warning(f"벤치마크 계산 실패: {str(e)}, 알파/베타 스킵")
```

**Why It Matters**:
- Benchmark calculation failures are silently ignored
- No visibility into whether calculations succeeded or failed
- Helps diagnose why alpha/beta might be None in results

---

## FILE 2: portfolio_service.py

### 4. Exchange Rate Loading for Portfolio (Lines 158-167)

**Location**: `calculate_dca_portfolio_returns()` method, start

**Operation Description**:
- Loads exchange rates for all required currencies in portfolio
- Critical for accurate DCA calculation with multi-currency assets

**Current Logging**:
- ⚠️ PARTIAL - Logs individual ticker currency info (line 153)
- ❌ Missing: No logging of which currencies need loading
- ❌ Missing: No logging of actual exchange rates loaded
- ❌ Missing: No logging of load success/failure details

**Suggested Logging Statements**:
```python
# After identifying required currencies (line 160):
required_currencies = list(set(ticker_currencies.values()) - {'USD'})
if required_currencies:
    logger.info(f"포트폴리오 환율 로딩 필요: {', '.join(required_currencies)}")
    for currency in required_currencies:
        logger.debug(f"  종목 통화: {currency}")
else:
    logger.debug("포트폴리오 모든 종목이 USD, 환율 변환 불필요")

# After loading exchange rates (after line 167):
logger.info(f"환율 데이터 로딩 완료: {len(required_currencies)}개 통화")
for currency, rates_dict in exchange_rates_by_currency.items():
    if rates_dict:
        start_rate = next(iter(rates_dict.values()))
        end_rate = list(rates_dict.values())[-1]
        logger.debug(f"  {currency}: {start_rate:.4f} ~ {end_rate:.4f} (기간 {len(rates_dict)}일)")
```

**Why It Matters**:
- Exchange rate loading is async and can fail silently
- No visibility into rate values used for conversions
- Essential for auditing multi-currency portfolio calculations

---

### 5. DCA Execution - First Day (Lines 285-312)

**Location**: `calculate_dca_portfolio_returns()` method, first day logic

**Operation Description**:
- Executes initial investment (lump sum or DCA first payment)
- Calculates initial shares based on price and investment amount

**Current Logging**:
- ✅ GOOD - Has logging at lines 302 and 310
- ❌ Missing: No logging of failed price lookups
- ❌ Missing: No logging of share calculation details

**Suggested Logging Enhancements**:
```python
# After checking price availability (line 291):
if unique_key not in current_prices:
    symbol = dca_info[unique_key]['symbol']
    logger.warning(f"첫 투자 날짜 {current_date.date()}: {symbol} 가격 데이터 없음, 스킵")
    continue

# After share calculation (line 299):
logger.debug(f"  {symbol} 초기 주식 계산: ${invest_amount:,.2f} / ${price:.2f} = {shares[unique_key]:.4f}주")

# For DCA specific (after line 310):
info = dca_info[unique_key]
next_dca_date = get_next_nth_weekday(current_date, period_type, info['interval_weeks'], original_nth)
logger.debug(f"  {symbol} DCA 일정: 다음 매수 예정 {next_dca_date.date()}")
```

**Why It Matters**:
- Initial investment failure is silently skipped
- Share calculation details help verify DCA math
- Next DCA date helps track schedule execution

---

### 6. DCA Periodic Purchase Execution (Lines 315-378)

**Location**: `calculate_dca_portfolio_returns()` method, DCA loop

**Operation Description**:
- Executes periodic DCA purchases according to schedule
- Tracks DCA execution count and dates

**Current Logging**:
- ✅ GOOD - Has substantial logging (lines 369-375, 377)
- ⚠️ PARTIAL - Missing details on some decision points

**Suggested Logging Enhancements**:
```python
# After DCA decision point calculation (after line 346):
if current_date >= next_dca_date and prev_date < next_dca_date:
    logger.debug(f"DCA 실행 조건 충족: {symbol}, 현재={current_date.date()}, "
                 f"다음예정={next_dca_date.date()}, 이전={prev_date.date() if prev_date else 'None'}")

# When executed_count >= dca_periods (add to line 353-377):
else:
    logger.debug(f"DCA 완료: {symbol}, 실행 횟수 {executed_count}/{info['dca_periods']}")

# Add after line 375 for next scheduled:
next_scheduled_str = next_scheduled.strftime('%Y-%m-%d') if next_scheduled else 'N/A'
logger.debug(f"  {symbol} 다음 DCA 예정일: {next_scheduled_str}")
```

**Why It Matters**:
- DCA is complex with multiple date comparisons
- Helps verify schedule is executing correctly
- Aids debugging missed or duplicate executions

---

### 7. Rebalancing Trigger Check (Lines 379-387)

**Location**: `calculate_dca_portfolio_returns()` method, rebalancing section start

**Operation Description**:
- Determines if current date triggers a rebalancing event
- Complex logic involving frequency, original Nth weekday, last rebalance date

**Current Logging**:
- ⚠️ PARTIAL - Sets original_nth with debug log (lines 381-383)
- ❌ Missing: No logging of rebalance decision result
- ❌ Missing: No logging of why rebalancing was/wasn't triggered

**Suggested Logging Statements**:
```python
# After should_rebalance check (after line 387):
if should_rebalance and len(target_weights) > 1:
    logger.info(f"리밸런싱 트리거 날짜: {current_date.date()}, "
                f"주기: {rebalance_frequency}, 자산 수: {len(target_weights)}")
    logger.debug(f"  마지막 리밸런싱: {last_rebalance_date.date() if last_rebalance_date else 'None'}")
elif should_rebalance and len(target_weights) <= 1:
    logger.debug(f"리밸런싱 날짜이지만 자산 {len(target_weights)}개 (최소 2개 필요)")
else:
    if current_date.date() % 5 == 0:  # Sample logging every 5 days to avoid spam
        logger.debug(f"리밸런싱 아님: {current_date.date()}, "
                     f"다음 예정: {last_rebalance_date.date() if last_rebalance_date else 'N/A'}")
```

**Why It Matters**:
- Rebalancing is critical for portfolio performance
- Silent failures cause users to think rebalancing happened when it didn't
- Complex Nth weekday logic is prone to bugs

---

### 8. Rebalancing Weight Adjustment (Lines 389-436)

**Location**: `calculate_dca_portfolio_returns()` method, rebalancing target weight adjustment

**Operation Description**:
- Adjusts target weights when some stocks are delisted
- Scales remaining tradeable stocks proportionally

**Current Logging**:
- ✅ GOOD - Has info level logging (lines 416-420)
- ⚠️ PARTIAL - Missing: No logging at start of rebalancing
- ❌ Missing: No logging of calculated scaling factors summary

**Suggested Logging Enhancements**:
```python
# Add at start of rebalancing (before line 389):
current_values = {}
for unique_key in shares.keys():
    if unique_key in current_prices:
        value = shares[unique_key] * current_prices[unique_key]
        current_values[unique_key] = value
total_current_value = sum(current_values.values()) + available_cash
logger.info(f"리밸런싱 실행 {current_date.date()}: 포트폴리오 가치 ${total_current_value:,.2f}")
logger.debug(f"  목표 비중: {dict(target_weights)}")
logger.debug(f"  현재 비중 (계산 전): {current_values}")

# Add after scaling_factor calculation (around line 405):
if tradeable_weight_sum > 0:
    logger.debug(f"상장폐지 종목 제외 후 스케일링: {scaling_factor:.4f}배 적용")
```

**Why It Matters**:
- Delisting logic is complex and affects weight calculations
- No visibility into what weights were adjusted
- Helps verify rebalancing math

---

### 9. Rebalancing Trade Execution (Lines 438-595)

**Location**: `calculate_dca_portfolio_returns()` method, rebalancing trade execution

**Operation Description**:
- Executes actual buy/sell trades to achieve target weights
- Calculates and applies trading commissions
- Records trade history

**Current Logging**:
- ⚠️ PARTIAL - Logs completion summary (lines 587, 589, 594)
- ❌ Missing: No logging of individual buy/sell trades
- ❌ Missing: No logging of commission calculations
- ❌ Missing: No logging of stock vs cash adjustments

**Suggested Logging Statements**:
```python
# Before trade execution loop (after line 464):
logger.debug(f"리밸런싱 거래 실행: 총 포트폴리오 가치 ${total_portfolio_value:,.2f}")

# Inside stock processing (after line 522):
if abs(target_value - current_value) / total_portfolio_value > TradingThresholds.REBALANCING_THRESHOLD_PCT:
    shares_diff = (target_value / price) - shares[unique_key]
    action_type = "매수" if shares_diff > 0 else "매도"
    logger.info(f"  리밸런싱 거래: {symbol} {action_type} "
                f"{abs(shares_diff):.4f}주 @ ${price:.2f} (목표가: ${target_value:,.2f}, 현재: ${current_value:,.2f})")

# After commission calculation (after line 545):
if total_commission_cost > 0:
    logger.debug(f"리밸런싱 수수료: ${total_commission_cost:,.2f}")

# Add before line 587:
if rebalance_trades:
    logger.info(f"리밸런싱 완료: {current_date.date()}, 거래 {trades_in_rebalance}건, 수수료 ${total_commission_cost:,.2f}")
```

**Why It Matters**:
- Rebalancing trades directly impact portfolio performance
- Commission calculation is a common source of errors
- Individual trade logging essential for auditing

---

### 10. Currency Conversion During Rebalancing (Lines 215-248)

**Location**: `calculate_dca_portfolio_returns()` method, price conversion inside loop

**Operation Description**:
- Converts daily prices from original currency to USD
- Uses cached exchange rates with fallback logic
- Called every trading day for each stock

**Current Logging**:
- ⚠️ PARTIAL - Has debug log for successful conversion (line 242)
- ✅ GOOD - Has warning for cached fallback (line 232)
- ✅ GOOD - Has error for missing rates (line 234)
- ❌ Missing: No logging of exchange rate source (current vs cached)

**Suggested Logging Enhancements**:
```python
# Add summary after all daily price conversions (after line 248):
converted_count = len(current_prices)
if converted_count > 0:
    logger.debug(f"{current_date.date()}: {converted_count}개 종목 가격 변환 완료")

# Enhance line 242:
logger.debug(f"{symbol} 가격 변환: {currency} {raw_price:.2f} -> ${converted_price:.2f} "
             f"(환율: {exchange_rate:.4f}, 직접/USD 변환)")

# Enhance line 232:
logger.warning(f"{symbol} ({currency}): {current_date.date()} 환율 없음, "
               f"캐시된 환율 {exchange_rate:.4f} 사용")
```

**Why It Matters**:
- Exchange rate source affects backtest accuracy
- Fallback usage should be visible for audit trails
- Helps identify dates with missing rate data

---

### 11. Delisting Detection and Handling (Lines 250-283)

**Location**: `calculate_dca_portfolio_returns()` method, delisting tracking

**Operation Description**:
- Detects when stocks stop trading (delisting)
- Uses last valid prices when current data unavailable
- Critical for long-running backtests with corporate actions

**Current Logging**:
- ✅ GOOD - Has warning log for delisting (lines 267-272)
- ✅ GOOD - Has debug log for using last price (lines 280-282)
- ❌ Missing: No logging of price age/staleness
- ❌ Missing: No logging of delisted stock count summary

**Suggested Logging Enhancements**:
```python
# Add at delisting detection (after line 273):
logger.info(f"{symbol}이 상장폐지로 판단됨, 마지막 유효 가격 ${last_valid_prices[unique_key]:.2f} 유지 "
            f"({days_without_price}일 가격 데이터 없음)")

# Add rebalancing section to log delisted count:
# (after line 393 where delisted_weight_sum is calculated):
if delisted_stocks:
    logger.info(f"리밸런싱 시 상장폐지 종목: {len(delisted_stocks)}개, "
                f"원래 비중 {delisted_weight_sum:.2%} → 거래 불가")
```

**Why It Matters**:
- Delisting significantly affects portfolio performance
- Users need to know which stocks were delisted
- Helps distinguish between bad strategy and corporate events

---

## Summary Table

| # | File | Method | Lines | Operation | Logging Status | Severity |
|---|------|--------|-------|-----------|----------------|----------|
| 1 | backtest_engine.py | `_convert_to_usd()` | 191-224 | Currency conversion | ❌ None | CRITICAL |
| 2 | backtest_engine.py | `_build_strategy()` | 226-263 | Strategy param override | ⚠️ Partial | HIGH |
| 3 | backtest_engine.py | `_convert_result_to_response()` | 402-428 | Benchmark alpha/beta | ❌ None | MEDIUM |
| 4 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 158-167 | Exchange rate loading | ⚠️ Partial | CRITICAL |
| 5 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 285-312 | DCA first day execution | ✅ Good | LOW |
| 6 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 315-378 | DCA periodic execution | ✅ Good | LOW |
| 7 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 379-387 | Rebalancing trigger | ⚠️ Partial | HIGH |
| 8 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 389-436 | Rebalancing weight adjust | ✅ Good | MEDIUM |
| 9 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 438-595 | Rebalancing trade execution | ⚠️ Partial | HIGH |
| 10 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 215-248 | Currency conversion in loop | ⚠️ Partial | HIGH |
| 11 | portfolio_service.py | `calculate_dca_portfolio_returns()` | 250-283 | Delisting detection | ✅ Good | MEDIUM |

