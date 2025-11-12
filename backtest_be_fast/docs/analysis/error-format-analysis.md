# 에러 메시지 불일치 분석 보고서

## 요약

백엔드 서비스 파일 전반에 걸쳐 일관되지 않은 에러 메시지 형식의 여러 카테고리를 발견했습니다. 문제점:
- 혼합된 에러 메시지 스타일 (한국어만, 영어만, 혼합)
- 일관되지 않은 대문자 사용 및 구두점 패턴
- 유사한 에러에 대한 다른 에러 메시지 구조
- 서비스 전반에 걸쳐 일관되지 않은 로깅 패턴
- 에러 메시지의 가변적인 컨텍스트 포함

---

## 카테고리별 상세 발견사항

### 1. 유효성 검증 에러 (Error Code: 422/400)

#### A. 전략 파라미터 유효성 검증
파일: `app/services/strategy_service.py`

| 라인 | 현재 형식 | 에러 타입 | 문제점 |
|------|---|---|---|
| 199 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | 한국어, 마침표 없음 |
| 205 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | 한국어, 중복 (199와 동일) |
| 241 | `"지원하지 않는 전략: {strategy_name}"` | ValueError | 한국어, 중복 |
| 257-259 | `"파라미터 {param_name}을(를) {param_type.__name__} 타입으로 변환할 수 없습니다"` | ValueError | 한국어, 상세함 |
| 262-264 | `"{param_name}의 값 {value}는 최소값 {param_info['min']}보다 작습니다"` | ValueError | 한국어, 구조화됨 |
| 266-268 | `"{param_name}의 값 {value}는 최대값 {param_info['max']}보다 큽니다"` | ValueError | 한국어, 구조화됨 |
| 291-294 | `"{strategy_name} 전략에서 {left_param}({params[left_param]})는 {right_param}({params[right_param]})보다 작아야 합니다"` | ValueError | 한국어, 매우 긺 |

문제점:
- 라인 199, 205, 241: 동일한 메시지가 다른 컨텍스트에서 발생 (중복)
- 메시지 구조가 다양함: 일부는 파라미터 세부사항 포함, 일부는 미포함
- 길이 불일치: 단순 vs. 매우 상세

권장 표준 형식:
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

#### B. 포트폴리오 유효성 검증
파일: `app/schemas/schemas.py`

| 라인 | 현재 형식 | 에러 타입 | 문제점 |
|------|---|---|---|
| 73 | `'amount와 weight는 동시에 입력할 수 없습니다. 하나만 입력하세요.'` | ValueError | 한국어, 지시 톤 |
| 92 | `'주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야 합니다.'` | ValueError | 한국어, 상세 규칙 |
| 99 | `'투자 방식은 lump_sum 또는 dca만 가능합니다.'` | ValueError | 한국어, enum 값 |
| 106 | `'자산 타입은 stock 또는 cash만 가능합니다.'` | ValueError | 한국어, enum 값 |
| 113 | `'DCA 주기는 {", ".join(FREQUENCY_MAP.keys())} 중 하나여야 합니다.'` | ValueError | 한국어, 동적 값 |
| 130 | `'포트폴리오는 최소 1개 종목을 포함해야 합니다.'` | ValueError | 한국어, 제약조건 |
| 142 | `'중복된 종목이 있습니다: {", ".join(sorted(duplicates))}. 같은 종목은 한 번만 추가할 수 있습니다.'` | ValueError | 한국어, 긴 메시지 |
| 148 | `'포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가.'` | ValueError | 한국어, 중복 개념 |
| 155 | `'종목 비중 합계가 95-105% 범위를 벗어났습니다. 현재: {total_weight:.1f}%'` | ValueError | 한국어, 구체적 컨텍스트 |
| 159 | `'총 투자 금액은 0보다 커야 합니다.'` | ValueError | 한국어, 제약조건 |
| 168 | `'날짜는 YYYY-MM-DD 형식이어야 합니다.'` | ValueError | 한국어, 형식 요구사항 |
| 178 | `'종료 날짜는 시작 날짜보다 이후여야 합니다.'` | ValueError | 한국어, 날짜 로직 |
| 180 | `'백테스트 기간은 최대 {settings.max_backtest_duration_years}년으로 제한됩니다.'` | ValueError | 한국어, 동적 제한 |

문제점:
- 일관되지 않은 구두점 (일부는 마침표로 끝나고, 일부는 지시 톤)
- 명령형 ("해야 합니다") vs. 서술형 ("합니다") 혼합
- 라인 142와 148은 제약조건 혼합에 대한 중복 개념 포함
- 일관된 에러 코드나 식별자 없음

권장 표준 형식:
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

### 2. 데이터 미발견 에러 (Error Code: 404)

파일: `app/utils/data_fetcher.py`, `app/core/exceptions.py`, `app/services/chart_data_service.py`

| 라인 | 파일 | 현재 형식 | 문제점 |
|---|---|---|---|
| 198 | data_fetcher.py | `f"'{ticker}' 종목에 대한 {start_str}부터 {end_str}까지의 데이터를 찾을 수 없습니다. 오류: {'; '.join(error_messages)}"` | 매우 김, 에러 세부사항 포함 |
| 230 | data_fetcher.py | `f"'{ticker}'는 유효하지 않은 종목 심볼입니다."` | 유효하지 않은 심볼에 대한 다른 메시지 |
| 234 | data_fetcher.py | `f"'{ticker}' 종목의 데이터가 부족합니다. ({len(data)}개 레코드)"` | 레코드 수 포함 |
| 261 | data_fetcher.py | `f"'{ticker}' 종목의 필수 데이터 'Close'가 없습니다."` | 필수 컬럼 누락 |
| 279 | data_fetcher.py | `f"'{ticker}' 종목의 유효한 데이터가 없습니다."` | 일반적인 빈 데이터 메시지 |
| 50-54 | exceptions.py | `f"'{symbol}' 종목의 데이터를 찾을 수 없습니다. (기간: {start_date} ~ {end_date})"` | 날짜 범위가 포함된 다른 형식 |
| 221 | chart_data_service.py | `f"'{ticker}' 종목의 가격 데이터를 찾을 수 없습니다."` | 일반적, 날짜 컨텍스트 없음 |

문제점:
- 일관되지 않은 메시지 구조 (일부는 날짜 포함, 일부는 미포함)
- 유사한 상황에 대한 다른 표현 ("찾을 수 없습니다" vs "없습니다")
- 에러 컨텍스트의 가변적인 세부 수준
- 일부는 에러 하위 이유 포함, 일부는 일반적

권장 표준 형식:
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

### 3. 통화 변환 에러

파일: `app/utils/currency_converter.py`

| 라인 | 현재 형식 | 에러 타입 | 문제점 |
|---|---|---|---|
| 157 | `"USD는 환율 변환이 필요하지 않습니다"` | ValueError | 마침표 없음, 특정 케이스 |
| 161 | `"지원하지 않는 통화: {currency}"` | ValueError | 짧음, 마침표 없음 |
| 165 | `"{currency} 환율 티커가 정의되지 않았습니다"` | ValueError | 티커 조회 관련 |
| 182 | `"{currency} 환율 데이터를 로드할 수 없습니다"` | ValueError | 로드 실패, 마침표 없음 |
| 229 | `f"{ticker} 통화 정보 조회 실패: {e}, USD로 가정"` | logger.warning | 컨텍스트 포함하지만 경고로 |
| 238 | `f"지원하지 않는 통화: {currency}, 변환 없이 진행"` | logger.warning | 라인 161 중복 |
| 301 | `f"통화 변환 중 오류: {e}, 원본 데이터 사용"` | logger.error | 폴백이 있는 일반 에러 |
| 348 | `f"지원하지 않는 통화 건너뛰기: {currency}"` | logger.warning | 액션 지향 메시지 |
| 364 | `f"{currency} 환율 데이터 없음, 건너뛰기"` | logger.warning | 단축 형식 |
| 387 | `f"{currency} 환율 로드 실패: {e}, 건너뛰기"` | logger.warning | 예외 세부사항 포함 |

문제점:
- 라인 161과 238: ValueError와 logger.warning 모두로 발생하는 동일한 메시지
- 라인 348과 364: 유사한 상황에 대한 다른 표현
- 일관되지 않게 마침표 누락
- 일부는 예외 세부사항 ({e}) 포함, 일부는 미포함
- 유사한 조건에 대한 에러 (raise)와 경고 (logger) 혼합

권장 표준 형식:
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

### 4. 네트워크 및 API 에러 (Error Code: 429/503)

파일: `app/services/news_service.py`, `app/utils/data_fetcher.py`

| 라인 | 파일 | 현재 형식 | 문제점 |
|---|---|---|---|
| 115 | data_fetcher.py | `f"야후 파이낸스 연결 오류: {str(e)}"` | 특정 제공자 언급 |
| 118 | data_fetcher.py | `f"'{ticker}' 종목 데이터 수집 실패: {str(e)}"` | 원본 예외 포함 |
| 158 | news_service.py | `f"네트워크 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}"` | 재시도 컨텍스트 포함 |
| 163 | news_service.py | `f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}"` | 최종 시도 메시지 |
| 164 | news_service.py | `f"네트워크 연결 실패 (최대 재시도 초과): {str(e)}"` | 라인 163 중복 |
| 166 | news_service.py | `f"네이버 뉴스 검색 오류: {str(e)}"` | 일반 검색 에러 |
| 119 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | 설정 문제 |
| 60 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | 중복 메시지 (경고) |

문제점:
- 라인 163-164: 예외 핸들러에서 동일한 에러 메시지
- 라인 60과 119: logger.warning과 raise Exception에서 동일한 메시지
- 일관되지 않은 예외 세부사항 포함 ({e} vs {str(e)})
- 라인 158과 163: 둘 다 재시도를 처리하지만 다른 메시지 형식
- 일관된 에러 코드나 재시도 전략 표시 없음

권장 표준 형식:
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

### 5. 설정 에러

파일: `app/services/news_service.py`, `app/api/v1/endpoints/backtest.py`

| 라인 | 파일 | 현재 형식 | 에러 타입 | 문제점 |
|---|---|---|---|---|
| 60 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | logger.warning | 초기화 경고 |
| 119 | news_service.py | `"네이버 API 키가 설정되지 않았습니다."` | Exception | 실행 에러 |
| 137 | backtest.py | `"상장일 검증 실패: {validation_errors}"` | ValidationError | 유효성 검증 실패 |

문제점:
- 경고와 예외 모두에 사용되는 동일한 메시지 (라인 60, 119)
- 라인 137: 메시지에 포함된 에러 코드이지만 일관되지 않게 형식화됨
- 쉬운 식별/지역화를 위한 에러 코드 없음

권장 표준 형식:
```python
# Pattern 1 (Missing Configuration - Initialization)
"API 설정이 누락되었습니다: {api_name}. 환경 변수를 설정하세요: {var_name}"

# Pattern 2 (Missing Configuration - Runtime)
"필수 설정이 누락되었습니다: {config_name}. 작업을 계속할 수 없습니다."
```

---

### 6. 비즈니스 로직 에러

파일: `app/services/portfolio_service.py`, `app/services/backtest_engine.py`

| 라인 | 파일 | 현재 형식 | 에러 타입 | 문제점 |
|---|---|---|---|---|
| 130 | portfolio_service.py | `"유효한 데이터가 없습니다."` | ValueError | 너무 일반적 |
| 694 | portfolio_service.py | `f"계산된 포트폴리오 값 개수({len(portfolio_values)})가 날짜 개수({len(valid_dates)})와 일치하지 않습니다."` | ValueError | 매우 구체적, 내부용 |
| 759 | portfolio_service.py | `'포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다.'` | ValidationError | 중복 유효성 검증 |
| 860 | portfolio_service.py | `"모든 종목의 백테스트가 실패했습니다."` | ValueError | 치명적 실패 |
| 1177 | portfolio_service.py | `"포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다."` | ValueError | 데이터 로딩 실패 |
| 137 | backtest_engine.py | `"Invalid backtest result"` | Exception | 영어, 일반적 |
| 140 | backtest_engine.py | `f"백테스트 실행 중 오류: {e}"` | logger.error | 일반 에러 |
| 146 | backtest_engine.py | `f"백테스트 전체 프로세스 오류: {e}"` | logger.error | 포괄 에러 |
| 164 | backtest_engine.py | `detail=str(e)` | HTTPException | 의미 있는 메시지 없음 |
| 169 | backtest_engine.py | `f"백테스트 실행 실패: {str(e)}"` | HTTPException | 일반 실패 |
| 187 | backtest_engine.py | `"가격 데이터를 찾을 수 없습니다."` | HTTPException | 티커 컨텍스트 없음 |

문제점:
- 라인 137 (backtest_engine.py): 한국어 메시지 중 영어 메시지
- 라인 694: 매우 내부적인 에러 메시지 (사용자 대면용이 아님)
- 라인 759와 validation_service.py 라인 91: 중복 개념 유효성 검증
- 라인 1177: "어떤 종목도"의 의미가 불명확 (none vs. any)
- 라인 140, 146, 169: 예외 세부사항이 포함된 일반 에러 메시지
- 라인 187: 티커 컨텍스트 누락

권장 표준 형식:
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

### 7. 로거 패턴 불일치

분석: 로깅 레벨 및 메시지에 일관성 부족

| 패턴 | 수 | 문제점 |
|---|---|---|
| `logger.info()` 성공 완료용 | 30개 이상 | 장황함, 세부 수준 일관되지 않음 |
| `logger.warning()` 복구 가능한 에러용 | 20개 이상 | 일부는 logger.warning 사용, 일부는 동일 조건에 예외 발생 |
| `logger.error()` 치명적 에러용 | 10개 이상 | 때로는 {e} 포함, 때로는 {str(e)}, 때로는 없음 |
| 로거 컨텍스트 누락 | 다양 | 추적용 에러 ID나 에러 코드 없음 |

불일치 예시:
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

## 문제점 요약

### 치명적 문제
1. 중복 메시지: 여러 위치에서 발생하는 동일한 에러 (strategy_service.py 라인 199, 205, 241)
2. 언어 혼합: 대부분 한국어에 가끔 영어 (backtest_engine.py 라인 137: "Invalid backtest result")
3. 일관되지 않은 에러 타입: 동일한 에러 조건이 예외와 경고 모두로 처리됨
4. 컨텍스트 누락: 일부 에러에 필요한 컨텍스트 부족 (backtest_engine.py 라인 187: 티커 없음)

### 주요 문제
1. 에러 코드 없음: 쉬운 조회 및 지역화를 위한 표준화된 에러 ID 없음
2. 가변적 메시지 구조: 관련 에러 타입에 대한 다른 형식
3. 일관되지 않은 구두점: 마침표 누락, 일관되지 않은 한국어 문법
4. 예외 세부사항 처리: 일부는 {e} 포함, 일부는 {str(e)}, 일부는 없음
5. 로깅 레벨 불일치: 유사한 에러가 다른 레벨에서 로깅됨

### 사소한 문제
1. 장황한 메시지: 일부 메시지가 너무 김 (예: portfolio_service.py 라인 142)
2. 내부 세부사항 노출: 에러 메시지에 구현 세부사항 포함 (라인 694)
3. 불명확한 표현: 일부 메시지의 모호한 한국어 표현
4. 일관되지 않은 형식: 파라미터 플레이스홀더가 다른 스타일 사용

---

## 권장사항

### 1. 에러 코드 시스템 생성
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

### 2. 에러 코드가 있는 예외 기본 클래스 생성
```python
class AppException(Exception):
    def __init__(self, error_code: str, **kwargs):
        self.error_code = error_code
        self.message = ERROR_CODES[error_code][1].format(**kwargs)
        super().__init__(self.message)
```

### 3. 메시지 형식 표준화
- 사용자 대면 메시지는 항상 한국어 사용
- 관련성이 있을 때 항상 컨텍스트 포함 (티커, 날짜 범위 등)
- 일관된 구두점 사용 (끝에 마침표, 혼합 문법 없음)
- 로그에는 에러 코드 포함하되 HTTP 응답에는 포함하지 않음

### 4. 메시지 템플릿 파일 생성
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

### 5. 로깅 모범 사례
```python
# 일관된 형식 사용
logger.error(f"[{error_code}] {message}", extra={"ticker": ticker})

# 항상 컨텍스트 포함
logger.warning(f"데이터 수집 실패: {symbol} - {error_reason}")

# 메시지에 원시 예외를 로깅하지 않음 (구조화된 로깅 사용)
logger.error(f"Error: {str(e)}")  # 나쁨
logger.error(f"Processing failed", exc_info=e)  # 좋음
```

---

## 우선순위 수정사항

### P0 (치명적 - 즉시 수정)
1. 중복 전략 유효성 검증 메시지 수정 (strategy_service.py)
2. 에러 처리 표준화: 동일 조건에 대한 혼합 예외/경고 제거
3. 모든 커스텀 예외에 에러 코드 추가

### P1 (높음 - 이번 스프린트에 수정)
1. 모든 에러 카테고리에 대한 메시지 템플릿 생성
2. 통화 변환기 에러 메시지 표준화
3. 일반 에러 메시지에 누락된 컨텍스트 추가

### P2 (중간 - 다음 스프린트에 수정)
1. 포트폴리오 유효성 검증 에러 메시지 리팩터링
2. 일관된 형식으로 모든 logger.error 호출 표준화
3. 로그에 에러 ID 추적 추가

### P3 (낮음 - 개선)
1. 긴 에러의 메시지 가독성 개선
2. 향후 번역을 위한 지역화 지원 추가
3. 개발자용 에러 코드 문서 추가
