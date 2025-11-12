# Error Message Inconsistency Analysis Report

## Summary
Found **multiple categories of inconsistent error message formats** across backend service files. Issues include:
- Mixed error message styles (Korean only, English only, mixed)
- Inconsistent capitalization and punctuation patterns
- Different error message structures for similar errors
- Inconsistent logging patterns across services
- Variable context inclusion in error messages

---

## DETAILED FINDINGS BY CATEGORY

### 1. VALIDATION ERRORS (Error Code: 422/400)

#### A. Strategy Parameter Validation
**File**: `app/services/strategy_service.py`

| Line | Current Format | Error Type | Issue |
|------|---|---|---|
| 199 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | Korean, no period |
| 205 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | Korean, duplicated (same as 199) |
| 241 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | Korean, duplicated |
| 257-259 | `"파라미터 {param_name}을(를) {param_type.__name__} 타입으로 변환할 수 없습니다"` | ValueError | Korean, detailed |
| 262-264 | `"{param_name}의 값 {value}는 최소값 {param_info['min']}보다 작습니다"` | ValueError | Korean, structured |
| 266-268 | `"{param_name}의 값 {value}는 최대값 {param_info['max']}보다 큽니다"` | ValueError | Korean, structured |
| 291-294 | `"{strategy_name} 전략에서 {left_param}({params[left_param]})는 {right_param}({params[right_param]})보다 작아야 합니다"` | ValueError | Korean, very long |

**Issues**:
- Line 199, 205, 241: Identical message but raised in different contexts (duplication)
- Message structure varies: some include parameter details, others don't
- Length inconsistency: simple vs. very detailed

**Suggested Standardized Format**:
```python
# Pattern 1 (Unsupported Strategy)
"지원하지 않는 전략입니다: {strategy_name}"

# Pattern 2 (Parameter Type Conversion)
"파라미터 '{param_name}'을(를) '{param_type}' 타입으로 변환할 수 없습니다."

# Pattern 3 (Value Out of Range)
"파라미터 '{param_name}'의 값이 범위를 벗어났습니다. (입력: {value}, 범위: {min}~{max})"

# Pattern 4 (Constraint Violation)
"전략 '{strategy_name}' 제약 조건 위반: '{left_param}' < '{right_param}' 필요"
```

---

#### B. Portfolio Validation
**File**: `app/schemas/schemas.py`

| Line | Current Format | Error Type | Issue |
|------|---|---|---|
| 73 | `'amount와 weight는 동시에 입력할 수 없습니다. 하나만 입력하세요.'` | ValueError | Korean, instruction tone |
| 92 | `'주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.'` | ValueError | Korean, detailed rules |
| 99 | `'투자 방식은 lump_sum 또는 dca만 가능합니다.'` | ValueError | Korean, enum values |
| 106 | `'자산 타입은 stock 또는 cash만 가능합니다.'` | ValueError | Korean, enum values |
| 113 | `'DCA 주기는 {", ".join(FREQUENCY_MAP.keys())} 중 하나여야 합니다.'` | ValueError | Korean, dynamic values |
| 130 | `'포트폴리오는 최소 1개 종목을 포함해야 합니다.'` | ValueError | Korean, constraint |
| 142 | `'중복된 종목이 있습니다: {", ".join(sorted(duplicates))}. 같은 종목은 한 번만 추가할 수 있습니다.'` | ValueError | Korean, long message |
| 148 | `'포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가.'` | ValueError | Korean, duplicated concept |
| 155 | `'종목 비중 합계가 95-105% 범위를 벗어났습니다. 현재: {total_weight:.1f}%'` | ValueError | Korean, specific context |
| 159 | `'총 투자 금액은 0보다 커야 합니다.'` | ValueError | Korean, constraint |
| 168 | `'날짜는 YYYY-MM-DD 형식이어야 합니다.'` | ValueError | Korean, format requirement |
| 178 | `'종료 날짜는 시작 날짜보다 이후여야 합니다.'` | ValueError | Korean, date logic |
| 180 | `'백테스트 기간은 최대 {settings.max_backtest_duration_years}년으로 제한됩니다.'` | ValueError | Korean, dynamic limit |

**Issues**:
- Inconsistent punctuation (some end with period, some with instruction tone)
- Mix of imperative ("해야 합니다") vs. declarative ("합니다") forms
- Line 142 and 148 contain overlapping concepts about constraint mixing
- No consistent error codes or identifiers

**Suggested Standardized Format**:
```python
# Pattern 1 (Mutually Exclusive)
"'{field1}' 및 '{field2}'를 동시에 입력할 수 없습니다."

# Pattern 2 (Invalid Format)
"'{field}' 형식이 올바르지 않습니다. (예상: {format}, 입력: {value})"

# Pattern 3 (Value Out of Range)
"'{field}' 값이 범위를 벗어났습니다. (범위: {min}~{max}, 입력: {value})"

# Pattern 4 (Duplicate Items)
"중복된 항목이 있습니다: {items}"

# Pattern 5 (Missing Required Item)
"'{field}'는 최소 {min_count}개 이상 필요합니다."

# Pattern 6 (Sum Validation)
"'{field}' 합계가 범위를 벗어났습니다. (범위: {min}~{max}%, 입력: {value}%)"
```

---

### 2. DATA NOT FOUND ERRORS (Error Code: 404)

**Files**: `app/utils/data_fetcher.py`, `app/core/exceptions.py`, `app/services/chart_data_service.py`

| Line | File | Current Format | Issue |
|---|---|---|---|
| 198 | data_fetcher.py | `f"'{ticker}' 종목에 대한 {start_str}부터 {end_str}까지의 데이터를 찾을 수 없습니다. 오류: {'; '.join(error_messages)}"` | Very long, includes error details |
| 230 | data_fetcher.py | `f"'{ticker}'는 유효하지 않은 종목 심볼입니다."` | Different message for invalid symbol |
| 234 | data_fetcher.py | `f"'{ticker}' 종목의 데이터가 부족합니다. ({len(data)}개 레코드)"` | Includes record count |
| 261 | data_fetcher.py | `f"'{ticker}' 종목의 필수 데이터 'Close'가 없습니다."` | Missing required column |
| 279 | data_fetcher.py | `f"'{ticker}' 종목의 유효한 데이터가 없습니다."` | Generic empty data message |
| 50-54 | exceptions.py | `f"'{symbol}' 종목의 데이터를 찾을 수 없습니다. (기간: {start_date} ~ {end_date})"` | Different format with date range |
| 221 | chart_data_service.py | `f"'{ticker}' 종목의 가격 데이터를 찾을 수 없습니다."` | Generic, no date context |

**Issues**:
- Inconsistent message structure (some with dates, some without)
- Different wording for similar situations ("찾을 수 없습니다" vs "없습니다")
- Variable level of detail in error context
- Some include error sub-reasons, others are generic

**Suggested Standardized Format**:
```python
# Pattern 1 (Data Not Found - Basic)
"'{ticker}' 데이터를 찾을 수 없습니다."

# Pattern 2 (Data Not Found - With Date Range)
"'{ticker}' 데이터를 찾을 수 없습니다. (기간: {start_date} ~ {end_date})"

# Pattern 3 (Insufficient Data)
"'{ticker}' 데이터가 불충분합니다. (필요: {min_records}개, 보유: {actual_records}개)"

# Pattern 4 (Missing Required Field)
"'{ticker}' 데이터에서 필수 필드를 찾을 수 없습니다: {missing_fields}"

# Pattern 5 (Invalid Symbol)
"유효하지 않은 종목 심볼: '{ticker}'"
```

---

### 3. CURRENCY CONVERSION ERRORS

**File**: `app/utils/currency_converter.py`

| Line | Current Format | Error Type | Issue |
|---|---|---|---|
| 157 | `"USD는 환율 변환이 필요하지 않습니다"` | ValueError | No period, specific case |
| 161 | `"지원하지 않는 통화: {currency}"` | ValueError | Short, no period |
| 165 | `"{currency} 환율 티커가 정의되지 않았습니다"` | ValueError | Specific to ticker lookup |
| 182 | `"{currency} 환율 데이터를 로드할 수 없습니다"` | ValueError | Load failure, no period |
| 229 | `f"{ticker} 통화 정보 조회 실패: {e}, USD로 가정"` | logger.warning | Has context but as warning |
| 238 | `f"지원하지 않는 통화: {currency}, 변환 없이 진행"` | logger.warning | Duplicate of line 161 |
| 301 | `f"통화 변환 중 오류: {e}, 원본 데이터 사용"` | logger.error | Generic error with fallback |
| 348 | `f"지원하지 않는 통화 건너뛰기: {currency}"` | logger.warning | Action-oriented message |
| 364 | `f"{currency} 환율 데이터 없음, 건너뛰기"` | logger.warning | Shortened format |
| 387 | `f"{currency} 환율 로드 실패: {e}, 건너뛰기"` | logger.warning | Includes exception details |

**Issues**:
- Lines 161 and 238: Same message raised as both ValueError and logger.warning
- Line 348 and 364: Different wording for similar situations
- Missing periods inconsistently
- Some include exception details ({e}), others don't
- Mix of error (raise) and warning (logger) for similar conditions

**Suggested Standardized Format**:
```python
# Pattern 1 (Unsupported Currency)
"지원하지 않는 통화: {currency}"

# Pattern 2 (Currency Not Applicable)
"{currency}는 환율 변환이 필요하지 않습니다."

# Pattern 3 (Currency Ticker Not Found)
"{currency} 환율 티커가 정의되지 않았습니다."

# Pattern 4 (Currency Data Load Failed)
"{currency} 환율 데이터를 로드할 수 없습니다. (오류: {error_reason})"

# Pattern 5 (Currency Info Lookup Failed - Warning)
"{ticker} 통화 정보 조회 실패: {currency}, USD로 진행합니다."

# Pattern 6 (Currency Skipped - Warning)
"{currency} 환율 데이터 없음: 해당 통화는 제외하고 진행합니다."
```

---

### 4. NETWORK & API ERRORS (Error Code: 429/503)

**Files**: `app/services/news_service.py`, `app/utils/data_fetcher.py`

| Line | File | Current Format | Issue |
|---|---|---|---|
| 115 | data_fetcher.py | `f"야후 파이낸스 연결 오류: {str(e)}"` | Specific provider mention |
| 118 | data_fetcher.py | `f"'{ticker}' 종목 데이터 수집 실패: {str(e)}"` | Includes original exception |
| 158 | news_service.py | `f"네트워크 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}"` | Includes retry context |
| 163 | news_service.py | `f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}"` | Final attempt message |
| 164 | news_service.py | `f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}"` | Duplicate of line 163 |
| 166 | news_service.py | `f"네이버 뉴스 검색 오류: {str(e)}"` | Generic search error |
| 119 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | Configuration issue |
| 60 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | Duplicated message (warning) |

**Issues**:
- Lines 163-164: Identical error messages in exception handler
- Lines 60 and 119: Same message in logger.warning and raise Exception
- Inconsistent exception detail inclusion ({e} vs {str(e)})
- Lines 158 and 163: Both handle retries but different message format
- No consistent error codes or retry strategy indication

**Suggested Standardized Format**:
```python
# Pattern 1 (API Configuration Missing)
"API 설정이 필요합니다: {api_name} (환경 변수: {var_name})"

# Pattern 2 (Connection Error - Retry Attempt)
"네트워크 오류가 발생했습니다. 재시도 중... (시도: {attempt}/{max_attempts})"

# Pattern 3 (Connection Error - Final Failure)
"네트워크 연결에 실패했습니다. (최대 재시도 횟수 초과, 마지막 오류: {last_error})"

# Pattern 4 (API Rate Limit)
"{api_name} API 요청 제한에 도달했습니다. ({retry_after}초 후 재시도)"

# Pattern 5 (Data Fetch Failed)
"{ticker} 데이터 수집 실패: {provider} (오류: {error})"
```

---

### 5. CONFIGURATION ERRORS

**File**: `app/services/news_service.py`, `app/api/v1/endpoints/backtest.py`

| Line | File | Current Format | Error Type | Issue |
|---|---|---|---|---|
| 60 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | logger.warning | Initialization warning |
| 119 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | Exception | Execution error |
| 137 | backtest.py | `"상장일 검증 실패: {validation_errors}"` | ValidationError | Validation failure |

**Issues**:
- Same message used for both warning and exception (lines 60, 119)
- Line 137: Error code included in message but inconsistently formatted
- No error codes for easy identification/localization

**Suggested Standardized Format**:
```python
# Pattern 1 (Missing Configuration - Initialization)
"API 설정이 누락되었습니다: {api_name}. 환경 변수를 설정하세요: {var_name}"

# Pattern 2 (Missing Configuration - Runtime)
"필수 설정이 누락되었습니다: {config_name}. 작업을 계속할 수 없습니다."
```

---

### 6. BUSINESS LOGIC ERRORS

**Files**: `app/services/portfolio_service.py`, `app/services/backtest_engine.py`

| Line | File | Current Format | Error Type | Issue |
|---|---|---|---|---|
| 130 | portfolio_service.py | `"유효한 데이터가 없습니다."` | ValueError | Too generic |
| 694 | portfolio_service.py | `f"계산된 포트폴리오 값 개수({len(portfolio_values)})가 날짜 개수({len(valid_dates)})와 일치하지 않습니다."` | ValueError | Very specific, internal |
| 759 | portfolio_service.py | `'포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다.'` | ValidationError | Duplicate validation |
| 860 | portfolio_service.py | `"모든 종목의 백테스트가 실패했습니다."` | ValueError | Critical failure |
| 1177 | portfolio_service.py | `"포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다."` | ValueError | Data loading failure |
| 137 | backtest_engine.py | `"Invalid backtest result"` | Exception | English, generic |
| 140 | backtest_engine.py | `f"백테스트 실행 중 오류: {e}"` | logger.error | Generic error |
| 146 | backtest_engine.py | `f"백테스트 전체 프로세스 오류: {e}"` | logger.error | Umbrella error |
| 164 | backtest_engine.py | `detail=str(e)` | HTTPException | No meaningful message |
| 169 | backtest_engine.py | `f"백테스트 실행 실패: {str(e)}"` | HTTPException | Generic failure |
| 187 | backtest_engine.py | `"가격 데이터를 찾을 수 없습니다."` | HTTPException | No ticker context |

**Issues**:
- Line 137 (backtest_engine.py): English message among Korean messages
- Line 694: Very internal error message (should not be user-facing)
- Line 759 and validation_service.py line 91: Duplicate concept validation
- Line 1177: Unclear what "어떤 종목도" means (none vs. any)
- Lines 140, 146, 169: Generic error messages with exception details
- Line 187: Missing ticker context

**Suggested Standardized Format**:
```python
# Pattern 1 (Generic Data Invalid)
"입력 데이터가 유효하지 않습니다: {reason}"

# Pattern 2 (Backtest Execution Failed)
"백테스트 실행 실패: {ticker} (오류: {error_reason})"

# Pattern 3 (All Items Failed)
"모든 {item_type}의 처리가 실패했습니다. (이유: {reason})"

# Pattern 4 (Data Unavailable)
"{item_type} 데이터를 사용할 수 없습니다: {ticker}"

# Pattern 5 (Processing Error)
"{process_name} 처리 중 오류가 발생했습니다: {error}"
```

---

### 7. LOGGER PATTERN INCONSISTENCIES

**Analysis**: Logging levels and messages lack consistency

| Pattern | Count | Issue |
|---|---|---|
| `logger.info()` for successful completion | 30+ | Verbose, not consistent in detail level |
| `logger.warning()` for recoverable errors | 20+ | Some use logger.warning, others raise exception for same condition |
| `logger.error()` for critical errors | 10+ | Sometimes includes {e}, sometimes {str(e)}, sometimes nothing |
| Missing logger context | Various | No error IDs or error codes for tracking |

**Example Inconsistencies**:
```python
# unified_data_service.py line 71 (logger.warning)
logger.warning(f"티커 정보 일괄 조회 실패: {str(e)}")

# portfolio_service.py line 1097 (logger.warning)
logger.warning(f"종목 {symbol}의 데이터가 없습니다.")

# news_service.py line 158 (logger.warning with context)
logger.warning(f"네트워크 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}")

# news_service.py line 163 (logger.error)
logger.error(f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}")
```

---

## SUMMARY OF ISSUES

### Critical Issues
1. **Duplicate Messages**: Same error raised in multiple locations (strategy_service.py lines 199, 205, 241)
2. **Mixed Languages**: Mostly Korean with occasional English (backtest_engine.py line 137: "Invalid backtest result")
3. **Inconsistent Error Types**: Same error condition handled as both exception and warning
4. **Missing Context**: Some errors lack necessary context (backtest_engine.py line 187: no ticker)

### Major Issues
1. **No Error Codes**: No standardized error IDs for easy lookup and localization
2. **Variable Message Structure**: Different formats for related error types
3. **Inconsistent Punctuation**: Missing periods, inconsistent Korean grammar
4. **Exception Detail Handling**: Some include {e}, others {str(e)}, others nothing
5. **Logging Level Inconsistency**: Similar errors logged at different levels

### Minor Issues
1. **Verbose Messages**: Some messages are too long (e.g., portfolio_service.py line 142)
2. **Internal Details Exposed**: Error messages contain implementation details (line 694)
3. **Unclear Wording**: Ambiguous Korean phrasing in some messages
4. **Inconsistent Formatting**: Parameter placeholders use different styles

---

## RECOMMENDATIONS

### 1. Create Error Code System
```python
# app/core/error_codes.py
ERROR_CODES = {
    "STRATEGY_NOT_FOUND": ("E001", "지원하지 않는 전략: {strategy}"),
    "INVALID_PARAMETER": ("E002", "파라미터 '{name}' 값이 올바르지 않습니다"),
    "CURRENCY_NOT_SUPPORTED": ("E003", "지원하지 않는 통화: {currency}"),
    "DATA_NOT_FOUND": ("E004", "'{item}' 데이터를 찾을 수 없습니다"),
    "API_CONFIG_MISSING": ("E005", "API 설정이 필요합니다: {api}"),
    # ... etc
}
```

### 2. Create Exception Base Class with Error Codes
```python
class AppException(Exception):
    def __init__(self, error_code: str, **kwargs):
        self.error_code = error_code
        self.message = ERROR_CODES[error_code][1].format(**kwargs)
        super().__init__(self.message)
```

### 3. Standardize Message Format
- Always use Korean for user-facing messages
- Always include context (ticker, date range, etc.) when relevant
- Use consistent punctuation (period at end, no mixed grammar)
- Include error codes in logs but not in HTTP responses

### 4. Create Message Templates File
```python
# app/core/message_templates.py
MESSAGES = {
    "validation": {
        "invalid_strategy": "지원하지 않는 전략입니다: {strategy}",
        "param_out_of_range": "파라미터 '{name}'이(가) 범위를 벗어났습니다. (범위: {min}~{max})",
    },
    "data": {
        "not_found": "'{item}' 데이터를 찾을 수 없습니다.",
        "not_found_with_date": "'{item}' 데이터를 찾을 수 없습니다. (기간: {start}~{end})",
    },
    # ... etc
}
```

### 5. Logging Best Practices
```python
# Use consistent format
logger.error(f"[{error_code}] {message}", extra={"ticker": ticker})

# Include context always
logger.warning(f"데이터 수집 실패: {symbol} - {error_reason}")

# Never log raw exceptions in message (use structured logging)
logger.error(f"Error: {str(e)}")  # BAD
logger.error(f"Processing failed", exc_info=e)  # GOOD
```

---

## PRIORITY FIXES

### P0 (Critical - Fix Immediately)
1. Fix duplicate strategy validation messages (strategy_service.py)
2. Standardize error handling: remove mixed exception/warning for same condition
3. Add error codes to all custom exceptions

### P1 (High - Fix This Sprint)
1. Create message templates for all error categories
2. Standardize currency converter error messages
3. Add missing context to generic error messages

### P2 (Medium - Fix Next Sprint)
1. Refactor portfolio validation error messages
2. Standardize all logger.error calls with consistent format
3. Add error ID tracking to logs

### P3 (Low - Polish)
1. Improve message readability in long errors
2. Add localization support for future translations
3. Add error code documentation for developers

