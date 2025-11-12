"""
데이터 로딩 관련 상수

**역할**:
- 데이터 캐싱, 재시도, API 호출 관련 설정값 정의
- 매직 넘버 제거로 유지보수성 향상
- 중앙화된 설정 관리

**상수 카테고리**:
1. CacheConfig: 캐시 TTL 및 설정
2. RetryConfig: 재시도 로직 설정
3. TradingThresholds: 거래 전략 임계값
4. DataValidation: 데이터 검증 기준

**사용 예**:
```python
from app.constants.data_loading import CacheConfig, RetryConfig

# 캐시 TTL 사용
ttl = CacheConfig.MEMORY_TTL_HISTORICAL

# 재시도 설정
for attempt in range(RetryConfig.MAX_RETRIES):
    ...
```
"""


class CacheConfig:
    """캐시 설정 관련 상수"""

    # 메모리 캐시 TTL (초 단위)
    MEMORY_TTL_HISTORICAL = 86400  # 24시간 - 과거 데이터
    MEMORY_TTL_RECENT = 3600  # 1시간 - 최근 데이터

    # DB 캐시 기본 설정
    DB_CACHE_DEFAULT_HOURS = 24  # 24시간

    # 뉴스 캐시 설정
    NEWS_CACHE_MAX_HOURS = 3  # 3시간
    NEWS_DEFAULT_DISPLAY = 20  # 기본 표시 개수


class RetryConfig:
    """재시도 로직 설정"""

    # API 호출 재시도
    MAX_RETRIES = 3  # 최대 재시도 횟수
    INITIAL_DELAY = 2.0  # 초기 지연 시간 (초)
    BACKOFF_MULTIPLIER = 1.0  # 선형 백오프 (2s, 4s, 6s)

    # 날짜 범위 확장
    DATE_EXPANSION_DAYS_SMALL = 3  # 작은 확장 (±3일)
    DATE_EXPANSION_DAYS_LARGE = 7  # 큰 확장 (±7일)

    # 타임아웃
    API_TIMEOUT_SECONDS = 10  # API 호출 타임아웃


class TradingThresholds:
    """거래 전략 임계값"""

    # RSI 전략
    RSI_OVERSOLD = 30  # 과매도 임계값
    RSI_OVERBOUGHT = 70  # 과매수 임계값

    # 상장폐지 감지
    DELISTING_THRESHOLD_DAYS = 30  # 30일 이상 데이터 없으면 상폐 의심

    # 환율 데이터
    EXCHANGE_RATE_LOOKBACK_DAYS = 30  # 환율 데이터 조회 여유 기간
    EXCHANGE_RATE_BUFFER_DAYS = 60  # 환율 데이터 로딩 버퍼 (기본 60일)

    # 리밸런싱 임계값
    REBALANCING_THRESHOLD_PCT = 0.0001  # 0.01% (리밸런싱 판단 기준)

    # 백테스트 데이터 검증
    MIN_DATA_POINTS = 5  # 최소 데이터 포인트 수


class PercentageConstants:
    """백분율 변환 관련 상수"""

    TO_PERCENT = 100  # 소수 → 백분율 (0.01 → 1%)
    FROM_PERCENT = 0.01  # 백분율 → 소수 (1% → 0.01)
