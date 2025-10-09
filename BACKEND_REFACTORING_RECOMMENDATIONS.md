# 백엔드 리팩터링 제안서

## 목차
1. [개요](#개요)
2. [중복 코드 및 분산된 로직](#중복-코드-및-분산된-로직)
3. [네이밍 불일치 및 혼동](#네이밍-불일치-및-혼동)
4. [불필요한 복잡성 및 파일 분산](#불필요한-복잡성-및-파일-분산)
5. [모델 및 스키마 중복](#모델-및-스키마-중복)
6. [에러 처리 불일치](#에러-처리-불일치)
7. [우선순위별 리팩터링 계획](#우선순위별-리팩터링-계획)

---

## 개요

백엔드 코드베이스를 분석한 결과, 다음과 같은 주요 문제점들이 발견되었습니다:
- 중복된 코드와 로직이 여러 파일에 분산되어 있음
- 동일한 개념에 대해 서로 다른 이름이 사용되는 네이밍 불일치
- 불필요하게 복잡한 파일 구조와 과도한 추상화
- 모델과 스키마의 중복 정의
- 일관성 없는 에러 처리

---

## 1. 중복 코드 및 분산된 로직

### 1.1 데이터 로딩 로직 중복

**문제점:**
- `backtest.py:296`, `backtest.py:379`, `backtest.py:451`: `load_ticker_data()` 반복 호출
- `portfolio_service.py:322`, `portfolio_service.py:734`: 동일한 데이터 로딩 패턴
- 데이터 소스 선택 로직이 여러 곳에 중복

**영향받는 파일:**
- `app/api/v1/endpoints/backtest.py` (Line 296, 379, 451)
- `app/services/portfolio_service.py` (Line 322, 734)
- `app/services/backtest_service.py` (Line 171)

**제안:**
```python
# app/services/data_service.py (새 파일)
class DataService:
    """중앙화된 데이터 로딩 서비스"""

    @staticmethod
    async def get_ticker_data(
        ticker: str,
        start_date: str,
        end_date: str,
        use_db_first: bool = True
    ) -> pd.DataFrame:
        """
        DB 우선, fallback to yfinance 패턴을 하나로 통합
        """
        if use_db_first:
            df = load_ticker_data(ticker, start_date, end_date)
            if df is not None and not df.empty:
                return df

        # Fallback to yfinance
        df = data_fetcher.get_stock_data(ticker, start_date, end_date)
        if df is None or df.empty:
            raise DataNotFoundError(ticker, start_date, end_date)
        return df
```

**예상 효과:**
- 코드 중복 제거: ~150 라인 감소
- 데이터 소스 변경 시 한 곳만 수정
- 테스트 용이성 증가

---

### 1.2 에러 처리 패턴 중복

**문제점:**
- `backtest.py:127-175`: try-except 블록이 과도하게 중첩
- `backtest.py:233-258`, `backtest.py:405-428`: 거의 동일한 에러 핸들링 로직 반복
- `portfolio_service.py:430-436`, `portfolio_service.py:671-677`: 동일한 에러 응답 패턴

**영향받는 파일:**
- `app/api/v1/endpoints/backtest.py` (Line 110-175, 210-258, 405-428)
- `app/services/portfolio_service.py` (Line 430-436, 671-677, 946-952)

**제안:**
```python
# app/api/v1/decorators.py (새 파일)
from functools import wraps
import logging

def handle_backtest_errors(func):
    """백테스트 API 공통 에러 핸들러 데코레이터"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except (DataNotFoundError, InvalidSymbolError, YFinanceRateLimitError, ValidationError) as e:
            if isinstance(e, ValidationError):
                raise HTTPException(status_code=422, detail=str(e))
            raise e
        except Exception as e:
            error_id = log_error_for_debugging(e, func.__name__, {})
            logger.error(f"[{error_id}] Unexpected error in {func.__name__}: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"예상치 못한 오류가 발생했습니다. (오류 ID: {error_id})"
            )
    return wrapper

# 사용 예시
@router.post("/chart-data")
@handle_backtest_errors
async def get_chart_data(request: BacktestRequest):
    backtest_result = await backtest_service.run_backtest(request)
    chart_data = await backtest_service.generate_chart_data(request, backtest_result)
    return chart_data
```

**예상 효과:**
- 에러 처리 코드 ~200 라인 감소
- 일관된 에러 응답 보장
- 유지보수성 향상

---

### 1.3 검증 로직 중복

**문제점:**
- `backtest.py:211-216`: 포트폴리오 검증 로직
- `schemas.py:123-144`: 동일한 포트폴리오 검증 로직
- `validation_service.py`: 검증 로직이 분산되어 있음

**영향받는 파일:**
- `app/api/v1/endpoints/backtest.py` (Line 211-216)
- `app/models/schemas.py` (Line 123-144)

**제안:**
- Pydantic 모델의 validator를 최대한 활용
- 비즈니스 검증은 서비스 레이어로 이동
- 중복 검증 제거

---

## 2. 네이밍 불일치 및 혼동

### 2.1 전략 이름 불일치

**문제점:**
다음과 같은 다양한 전략 이름 표기가 혼재:
- `sma_crossover` vs `SMAStrategy`
- `rsi_strategy` vs `RSIStrategy`
- `bollinger_bands` vs `BollingerBandsStrategy`
- `macd_strategy` vs `MACDStrategy`
- `ema_crossover` vs `EMAStrategy`
- `buy_and_hold` vs `BuyAndHoldStrategy`

**영향받는 파일:**
- `app/models/requests.py` (Line 11-18): Enum 정의
- `app/services/strategy_service.py` (Line 21-146): 전략 매핑
- `app/strategies/*.py`: 전략 클래스 이름

**제안:**
```python
# 통일된 네이밍 컨벤션 적용
class StrategyType(str, Enum):
    """전략 타입 - 스네이크 케이스로 통일"""
    SMA_CROSSOVER = "sma_crossover"
    RSI = "rsi"  # rsi_strategy → rsi로 단순화
    BOLLINGER_BANDS = "bollinger_bands"
    MACD = "macd"  # macd_strategy → macd로 단순화
    EMA_CROSSOVER = "ema_crossover"
    BUY_AND_HOLD = "buy_and_hold"

# strategy_service.py도 동일하게 수정
class StrategyService:
    def __init__(self):
        self._strategies = {
            'sma_crossover': {
                'class': SMAStrategy,
                'name': 'SMA Crossover',
                'description': '단순 이동평균 교차 전략',
                # ...
            },
            'rsi': {  # 변경됨
                'class': RSIStrategy,
                'name': 'RSI',
                'description': 'RSI 과매수/과매도 기반 전략',
                # ...
            },
            # ...
        }
```

**예상 효과:**
- API 사용자 입장에서 명확하고 일관된 전략 이름
- 불필요한 `_strategy` 접미사 제거로 간결성 증가

---

### 2.2 모델 필드 네이밍 불일치

**문제점:**
동일한 개념이 서로 다른 이름으로 사용됨:
- `ticker` vs `symbol`
- `initial_cash` vs `Initial_Value` vs `amount`
- `total_return_pct` vs `Return [%]` vs `Total_Return`
- `strategy` vs `strategy_name`

**영향받는 파일:**
- `app/models/requests.py` (Line 29): `ticker`
- `app/models/responses.py` (Line 12): `ticker`
- `app/models/schemas.py` (Line 65): `symbol`
- `app/services/portfolio_service.py` (Line 654): `original_symbol`

**제안:**
```python
# 일관된 네이밍 규칙 정립
# 1. 종목 식별자: ticker (외부 API용) vs symbol (내부 로직용)
#    → ticker로 통일 (yfinance도 ticker 사용)

# 2. 금액 관련:
#    - initial_cash: 초기 투자금
#    - final_equity: 최종 자산
#    - amount: 항목별 투자금액

# 3. 수익률:
#    - return_pct: 백분율 수익률 (일반)
#    - total_return_pct: 총 수익률
#    - annualized_return_pct: 연간 수익률

# 4. 전략:
#    - strategy: 전략 타입/이름 (일관되게 사용)
```

---

### 2.3 Exception 클래스명 중복

**문제점:**
- `app/core/exceptions.py`: `BacktestError`
- `app/core/custom_exceptions.py`: `BacktestValidationError`, `ValidationError`
- `app/models/schemas.py`: `BacktestError` (응답 모델)

**영향받는 파일:**
- `app/core/exceptions.py` (Line 1-6)
- `app/core/custom_exceptions.py` (Line 41-57)
- `app/models/schemas.py` (Line 244-247)

**제안:**
```python
# app/core/exceptions.py 통합
class BacktestException(Exception):
    """백테스트 관련 기본 예외"""
    pass

class BacktestHTTPException(HTTPException):
    """HTTP 응답이 필요한 백테스트 예외"""
    pass

# app/models/schemas.py
class BacktestErrorResponse(BaseModel):  # 이름 변경
    """백테스트 오류 응답 모델"""
    error: str
    code: str
```

---

## 3. 불필요한 복잡성 및 파일 분산

### 3.1 과도한 서비스 분산

**문제점:**
백테스트 서비스가 과도하게 분산되어 있음:
- `backtest_service.py`: 메인 서비스 (545 lines)
- `backtest/backtest_engine.py`: 백테스트 실행
- `backtest/optimization_service.py`: 최적화
- `backtest/chart_data_service.py`: 차트 데이터 생성
- `backtest/validation_service.py`: 검증

**영향받는 파일:**
- `app/services/backtest_service.py`
- `app/services/backtest/` 디렉토리 전체

**제안:**
```
현재 구조:
app/services/
├── backtest_service.py         (545 lines)
├── backtest/
│   ├── backtest_engine.py
│   ├── optimization_service.py
│   ├── chart_data_service.py
│   └── validation_service.py
├── portfolio_service.py        (1019 lines)
└── strategy_service.py         (229 lines)

제안 구조:
app/services/
├── backtest.py                 (통합: backtest 관련 모든 로직)
├── portfolio.py               (현재 portfolio_service.py)
└── strategy.py                (현재 strategy_service.py)

또는 기능별 분리:
app/services/
├── execution/
│   ├── backtest_executor.py   (백테스트 실행)
│   └── portfolio_executor.py  (포트폴리오 백테스트)
├── analysis/
│   ├── chart_generator.py     (차트 데이터)
│   └── optimizer.py           (최적화)
└── strategy.py
```

**이유:**
1. 현재 `backtest_service.py`는 단순히 하위 서비스들을 호출만 하는 facade 패턴
2. 각 하위 서비스가 너무 작아서 분리의 이점이 적음
3. 코드 탐색 시 여러 파일을 오가야 하는 불편함

**예상 효과:**
- 파일 수 감소: 5개 → 2~3개
- 관련 로직을 한 곳에서 확인 가능
- 간결한 구조

---

### 3.2 불필요한 Factory 및 Repository 추상화

**문제점:**
`backtest_service.py`에서 Repository와 Factory 패턴을 도입했으나:
- 실제로 다양한 구현체가 필요하지 않음
- 추상화의 이점을 활용하지 못함
- 코드 복잡도만 증가

**영향받는 파일:**
- `app/services/backtest_service.py` (Line 16-18, 119-132)
- `app/factories/` 디렉토리
- `app/repositories/` 디렉토리

**제안:**
```python
# 현재 (과도한 추상화)
class BacktestService:
    def __init__(self, service_factory_instance=None):
        self.service_factory = service_factory_instance or service_factory
        self.backtest_engine = self.service_factory.create_backtest_engine()
        self.optimization_service = self.service_factory.create_optimization_service()
        # ...

# 제안 (직접 사용)
class BacktestService:
    def __init__(self):
        self.data_repository = DataRepository()
        self.backtest_repository = BacktestRepository()
        # 필요시에만 직접 초기화
```

**이유:**
- YAGNI 원칙: 현재 요구사항에 맞지 않는 과도한 추상화
- 단일 구현체만 존재하는 상황에서 Factory 패턴은 불필요
- 테스트 시에만 DI가 필요하다면 생성자 파라미터로 충분

---

### 3.3 미사용 도메인 분석 코드

**문제점:**
`backtest_service.py`에 도메인 분석 관련 메서드들이 있으나:
- `run_backtest_with_domain_analysis()` (Line 206-227)
- `_enhance_backtest_result()` (Line 228-265)
- `_analyze_strategy_metadata()` (Line 267-292)
- 실제 API에서 호출되지 않음
- `self.strategy_domain_service`, `self.backtest_domain_service` 등 정의되지 않은 속성 참조

**영향받는 파일:**
- `app/services/backtest_service.py` (Line 206-540)
- `app/services/portfolio_service.py` (Line 954-1018): 동일한 패턴

**제안:**
1. **즉시 삭제**: API에서 사용되지 않고 미완성 코드
2. 또는 **별도 브랜치로 이동**: 향후 구현 예정이라면

**예상 효과:**
- 코드 라인 수 대폭 감소 (~400 lines)
- 혼란 감소

---

## 4. 모델 및 스키마 중복

### 4.1 요청 모델 중복

**문제점:**
포트폴리오 관련 요청 모델이 중복 정의됨:
- `models/requests.py`: `PortfolioAsset`, `UnifiedBacktestRequest`
- `models/schemas.py`: `PortfolioStock`, `PortfolioBacktestRequest`

**영향받는 파일:**
- `app/models/requests.py` (Line 137-171)
- `app/models/schemas.py` (Line 63-165)

**제안:**
```python
# requests.py와 schemas.py 통합
# → models/requests.py 하나로 통일

# models/requests.py
class PortfolioItem(BaseModel):
    """포트폴리오 구성 항목"""
    symbol: str
    amount: Optional[float] = None
    weight: Optional[float] = None
    investment_type: str = "lump_sum"
    dca_periods: int = 12
    asset_type: str = "stock"

class PortfolioBacktestRequest(BaseModel):
    """포트폴리오 백테스트 요청"""
    portfolio: List[PortfolioItem]
    start_date: Union[date, str]
    end_date: Union[date, str]
    strategy: StrategyType = StrategyType.BUY_AND_HOLD
    strategy_params: Optional[Dict[str, Any]] = None
    commission: float = 0.002
    rebalance_frequency: str = "monthly"
```

---

### 4.2 응답 모델 중복

**문제점:**
백테스트 결과 응답 형식이 파편화됨:
- `responses.py`: `BacktestResult` (Pydantic 모델, Line 9-100)
- `schemas.py`: `BacktestData`, `BacktestResponse` (Line 198-242)
- API 엔드포인트에서 직접 딕셔너리 반환

**영향받는 파일:**
- `app/models/responses.py` (Line 9-100)
- `app/models/schemas.py` (Line 198-242)
- `app/api/v1/endpoints/backtest.py` (Line 219-231, 327-336)

**제안:**
```python
# responses.py로 통합, schemas.py의 중복 제거
# API는 항상 Pydantic 모델 반환

@router.post("/portfolio")
async def run_portfolio_backtest(
    request: PortfolioBacktestRequest
) -> PortfolioBacktestResponse:  # 명확한 응답 타입
    result = await portfolio_service.run_portfolio_backtest(request)
    return result
```

---

### 4.3 에러 모델 중복

**문제점:**
에러 응답이 통일되지 않음:
- `responses.py`: `ErrorResponse`
- `schemas.py`: `BacktestError`, `StockPriceError`
- API에서 직접 `{"status": "error", "message": ...}` 반환

**영향받는 파일:**
- `app/models/responses.py` (Line 176-191)
- `app/models/schemas.py` (Line 244-276)
- `app/api/v1/endpoints/backtest.py` (Line 300-303, 340-344)

**제안:**
```python
# models/responses.py
class ErrorResponse(BaseModel):
    """통일된 에러 응답"""
    status: str = "error"
    error_code: str
    message: str
    detail: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

# 모든 API에서 일관되게 사용
```

---

## 5. 에러 처리 불일치

### 5.1 예외 클래스 파편화

**문제점:**
- `core/exceptions.py`: `BacktestError` (6 lines, 거의 사용 안 됨)
- `core/custom_exceptions.py`: HTTPException 기반 예외들 (75 lines)
- 일부 API는 HTTPException 직접 발생
- 일부는 딕셔너리 반환 (`{"status": "error"}`)

**영향받는 파일:**
- `app/core/exceptions.py`
- `app/core/custom_exceptions.py`
- `app/api/v1/endpoints/backtest.py` (Line 134, 155, 173)

**제안:**
```python
# core/exceptions.py로 통합, custom_exceptions.py 제거
class BacktestException(Exception):
    """백테스트 기본 예외"""
    pass

class DataNotFoundError(BacktestException, HTTPException):
    """데이터 없음"""
    def __init__(self, ticker: str, start_date: str, end_date: str):
        HTTPException.__init__(
            self,
            status_code=404,
            detail=f"'{ticker}' 데이터를 찾을 수 없습니다 ({start_date}~{end_date})"
        )

class ValidationError(BacktestException, HTTPException):
    """검증 실패"""
    def __init__(self, message: str):
        HTTPException.__init__(self, status_code=400, detail=message)

# 일관된 에러 처리 미들웨어
@app.exception_handler(BacktestException)
async def backtest_exception_handler(request, exc):
    return ErrorResponse(
        error_code=exc.__class__.__name__,
        message=str(exc)
    )
```

---

### 5.2 에러 로깅 불일치

**문제점:**
- 일부는 `log_error_for_debugging()` 사용 (error ID 생성)
- 일부는 직접 `logger.error()` 호출
- 일부는 로깅 없이 에러만 발생

**영향받는 파일:**
- `app/api/v1/endpoints/backtest.py` (Line 131, 160, 252, 340)
- `app/services/portfolio_service.py` (Line 202, 252, 431)

**제안:**
```python
# 일관된 에러 로깅 유틸리티
class ErrorLogger:
    @staticmethod
    def log_and_raise(
        error: Exception,
        context: str,
        metadata: Dict[str, Any],
        http_status: int = 500
    ):
        error_id = log_error_for_debugging(error, context, metadata)
        logger.error(f"[{error_id}] {context}: {error}")
        raise HTTPException(
            status_code=http_status,
            detail=f"{context} 오류 (ID: {error_id})"
        )

# 사용
try:
    result = await backtest_service.run_backtest(request)
except Exception as e:
    ErrorLogger.log_and_raise(
        e,
        "백테스트 실행",
        {"ticker": request.ticker},
        500
    )
```

---

## 6. 기타 개선 사항

### 6.1 환율 데이터 하드코딩

**문제점:**
`backtest.py:451`: `KRW=X` 티커가 하드코딩됨

**제안:**
```python
# config.py
class Settings(BaseSettings):
    # ...
    exchange_rate_ticker: str = "KRW=X"

# backtest.py
exchange_data = load_ticker_data(
    settings.exchange_rate_ticker,
    start_date,
    end_date
)
```

---

### 6.2 주가 변동성 임계값 매직 넘버

**문제점:**
`backtest.py:271`: `threshold: float = 5.0` 기본값이 하드코딩

**제안:**
```python
# config.py
class Settings(BaseSettings):
    # ...
    volatility_threshold_pct: float = 5.0

# backtest.py
async def get_stock_volatility_news(
    ticker: str,
    start_date: str,
    end_date: str,
    threshold: float = settings.volatility_threshold_pct
):
```

---

### 6.3 NaverNewsService의 TICKER_MAPPING 분리

**문제점:**
`naver_news.py:24-98`: 거대한 티커 매핑 딕셔너리가 클래스 내부에 하드코딩

**제안:**
```python
# data/ticker_mapping.json (새 파일)
{
  "US": {
    "AAPL": "애플",
    "MSFT": "마이크로소프트",
    ...
  },
  "KR": {
    "005930.KS": "삼성전자",
    "000660.KS": "SK하이닉스",
    ...
  }
}

# naver_news.py
class NaverNewsService:
    def __init__(self):
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret
        self.ticker_mapping = self._load_ticker_mapping()

    def _load_ticker_mapping(self) -> Dict[str, str]:
        with open('data/ticker_mapping.json') as f:
            data = json.load(f)
            return {**data['US'], **data['KR']}
```

---

## 7. 우선순위별 리팩터링 계획

### Priority 1 (즉시 수행 권장)

1. **미사용 코드 삭제**
   - `backtest_service.py`의 도메인 분석 관련 메서드 (~400 lines)
   - `portfolio_service.py`의 미완성 분석 메서드 (~100 lines)
   - **예상 시간:** 1시간
   - **리스크:** 낮음

2. **Exception 통합**
   - `exceptions.py`와 `custom_exceptions.py` 통합
   - **예상 시간:** 2시간
   - **리스크:** 낮음

3. **전략 이름 통일**
   - StrategyType Enum과 strategy_service 매핑 일치
   - **예상 시간:** 1시간
   - **리스크:** 중간 (API 변경 포함)

### Priority 2 (1주일 내 수행)

4. **에러 처리 데코레이터 도입**
   - 중복된 try-except 블록 제거
   - **예상 시간:** 4시간
   - **리스크:** 중간

5. **데이터 로딩 로직 통합**
   - DataService 신규 생성
   - **예상 시간:** 3시간
   - **리스크:** 중간

6. **모델/스키마 통합**
   - requests.py와 schemas.py 정리
   - **예상 시간:** 4시간
   - **리스크:** 중간

### Priority 3 (2주 내 수행)

7. **서비스 구조 재편**
   - backtest 관련 서비스 파일 통합 검토
   - **예상 시간:** 8시간
   - **리스크:** 높음 (대규모 변경)

8. **네이밍 통일**
   - ticker/symbol, amount/cash 등 일관성 확보
   - **예상 시간:** 6시간
   - **리스크:** 높음 (전체 코드베이스 영향)

### Priority 4 (장기)

9. **Factory/Repository 패턴 재검토**
   - 실제 필요성 검토 후 단순화
   - **예상 시간:** 8시간
   - **리스크:** 높음

10. **설정 외부화**
    - 하드코딩된 값들을 config로 이동
    - **예상 시간:** 3시간
    - **리스크:** 낮음

---

## 8. 예상 효과

### 코드 감소 예상
- **현재:** ~5,000 lines (services + api endpoints)
- **리팩터링 후:** ~3,500 lines (-30%)

### 파일 수 감소
- **현재:** 25+ 파일
- **리팩터링 후:** 15-18 파일

### 유지보수성 향상
- 중복 코드 제거로 버그 수정 시 단일 지점 수정
- 일관된 네이밍으로 코드 이해도 향상
- 명확한 에러 처리로 디버깅 시간 단축

### 성능
- 영향 없음 (구조 개선이 주 목적)

---

## 9. 리팩터링 시 주의사항

1. **테스트 우선**
   - 리팩터링 전 현재 동작을 검증하는 테스트 작성
   - 리팩터링 후 동일한 테스트가 통과하는지 확인

2. **점진적 변경**
   - 한 번에 하나의 Priority만 수행
   - 각 단계마다 커밋 및 테스트

3. **API 호환성**
   - 전략 이름 변경 등 API 변경은 deprecation 경고 추가
   - 버전 업데이트 고려

4. **문서 업데이트**
   - CLAUDE.md 업데이트
   - API 문서 업데이트

---

## 10. 결론

백엔드 코드베이스는 전반적으로 잘 구조화되어 있으나, 다음과 같은 개선이 필요합니다:

**핵심 문제:**
1. 중복 코드 (데이터 로딩, 에러 처리)
2. 네이밍 불일치 (전략 이름, 모델 필드)
3. 과도한 추상화 (불필요한 Factory/Repository)
4. 미사용/미완성 코드 (도메인 분석)
5. 모델/스키마 중복 정의

**권장 조치:**
- Priority 1-2 항목을 먼저 진행 (즉시 효과, 낮은 리스크)
- Priority 3-4는 충분한 테스트 후 진행

이 리팩터링을 통해 코드의 명확성, 유지보수성, 확장성이 크게 향상될 것으로 예상됩니다.
