"""
통화 상수 및 환율 매핑 (Currency Constants and Exchange Rate Mapping)

**역할**:
- 지원하는 통화 목록 중앙화
- 환율 데이터 티커 매핑 관리
- 단일 출처의 진실(Single Source of Truth) 제공

**통화 정책**:
- **USD**: 기준 통화, 환율 변환 불필요
- **직접 환율 (KRW, JPY, etc)**: 1 USD = X 통화 단위
- **USD 환율 (EURUSD, GBPUSD, etc)**: 1 통화 = X USD

**지원 통화** (13개):
- USD: 미국달러
- KRW: 한국원화
- JPY: 일본엔화
- EUR: 유로
- GBP: 영국파운드
- CNY: 중국위안화
- HKD: 홍콩달러
- TWD: 대만달러
- SGD: 싱가포르달러
- AUD: 호주달러
- CAD: 캐나다달러
- CHF: 스위스프랑
- INR: 인도루피

**사용 예**:
```python
from app.constants.currencies import SUPPORTED_CURRENCIES

# 통화 지원 여부 확인
if currency in SUPPORTED_CURRENCIES:
    ticker = SUPPORTED_CURRENCIES[currency]

# 환율 데이터 조회
if ticker := SUPPORTED_CURRENCIES.get(currency):
    # ticker 사용해서 yfinance 조회
```

**의존성**:
- yfinance: 환율 데이터 조회

**연관 컴포넌트**:
- Backend: app/services/backtest_engine.py (환율 변환)
- Backend: app/services/portfolio_service.py (다중 통화 포트폴리오)
"""

# 지원하는 통화 및 환율 티커 매핑
# 키: 통화 코드 (ISO 4217)
# 값: Yahoo Finance 티커 (None은 변환 불필요)
SUPPORTED_CURRENCIES = {
    'USD': None,           # 미국달러 (기준 통화)
    'KRW': 'KRW=X',        # 한국원화 (1 USD = X KRW)
    'JPY': 'JPY=X',        # 일본엔화 (1 USD = X JPY)
    'EUR': 'EURUSD=X',     # 유로 (1 EUR = X USD)
    'GBP': 'GBPUSD=X',     # 영국파운드 (1 GBP = X USD)
    'CNY': 'CNY=X',        # 중국위안화 (1 USD = X CNY)
    'HKD': 'HKD=X',        # 홍콩달러 (1 USD = X HKD)
    'TWD': 'TWD=X',        # 대만달러 (1 USD = X TWD)
    'SGD': 'SGD=X',        # 싱가포르달러 (1 USD = X SGD)
    'AUD': 'AUDUSD=X',     # 호주달러 (1 AUD = X USD)
    'CAD': 'CADUSD=X',     # 캐나다달러 (1 CAD = X USD)
    'CHF': 'CHFUSD=X',     # 스위스프랑 (1 CHF = X USD)
    'INR': 'INR=X',        # 인도루피 (1 USD = X INR)
}

# 환율 데이터 검색 설정
EXCHANGE_RATE_LOOKBACK_DAYS = 30  # 환율 데이터 누락 시 과거 검색 일수
