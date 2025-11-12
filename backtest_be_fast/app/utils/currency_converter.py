"""
환율 변환 유틸리티

**역할**:
- 주가 데이터를 원래 통화에서 USD로 변환
- 환율 데이터 로딩, 전처리, 캐싱 로직 중앙화
- 코드 중복 제거 (backtest_engine, portfolio_service)

**주요 기능**:
1. get_conversion_multiplier(): 통화별 변환 비율 계산
2. load_and_prepare_exchange_rates(): 환율 데이터 로딩 및 전처리
3. convert_dataframe_to_usd(): DataFrame 전체를 USD로 변환
4. load_multiple_exchange_rates(): 여러 통화 환율 일괄 로딩

**변환 정책**:
- **직접 환율** (KRW, JPY, CNY, etc.): 1 USD = X 통화 → 가격을 환율로 나누기
- **USD 환율** (EUR, GBP, AUD, etc.): 1 통화 = X USD → 가격에 환율 곱하기

**의존성**:
- app/constants/currencies.py: SUPPORTED_CURRENCIES 정의
- app/services/yfinance_db.py: 환율 데이터 로딩

**연관 컴포넌트**:
- Backend: app/services/backtest_engine.py (단일 종목 백테스트)
- Backend: app/services/portfolio_service.py (포트폴리오 백테스트)

**사용 예**:
```python
from app.utils.currency_converter import CurrencyConverter

# 단일 종목 변환
converter = CurrencyConverter()
usd_data = await converter.convert_dataframe_to_usd(
    ticker="005930.KS",
    data=krw_price_data,
    start_date="2023-01-01",
    end_date="2023-12-31"
)

# 여러 통화 환율 로딩 (포트폴리오용)
exchange_rates = await converter.load_multiple_exchange_rates(
    currencies=['KRW', 'JPY', 'EUR'],
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import Dict, Optional, Tuple
import pandas as pd

from app.constants.currencies import SUPPORTED_CURRENCIES, EXCHANGE_RATE_LOOKBACK_DAYS
from app.constants.data_loading import TradingThresholds
from app.services.yfinance_db import load_ticker_data, get_ticker_info_from_db

logger = logging.getLogger(__name__)


class CurrencyConverter:
    """환율 변환 유틸리티 클래스"""

    @staticmethod
    def get_conversion_multiplier(currency: str, exchange_rate: float) -> float:
        """
        통화 타입에 따라 USD 변환 비율을 계산합니다.

        Args:
            currency: 통화 코드 (ISO 4217)
            exchange_rate: Yahoo Finance에서 가져온 환율

        Returns:
            float: USD 변환 시 곱해야 할 비율

        Note:
            - EUR, GBP, AUD, CAD, CHF: XXXUSD=X 형태 (1 통화 = X USD) → 곱하기
            - KRW, JPY, CNY, etc.: XXX=X 형태 (1 USD = X 통화) → 나누기
        """
        # USD 환율 (XXXUSD=X): 통화에 환율을 곱함
        if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
            return exchange_rate

        # 직접 환율 (XXX=X): 통화를 환율로 나눔
        return 1.0 / exchange_rate if exchange_rate > 0 else 1.0

    @staticmethod
    def _normalize_date_to_datetime(date_value) -> datetime:
        """
        다양한 날짜 형식을 datetime 객체로 정규화합니다.

        Args:
            date_value: str, date, datetime, 또는 pd.Timestamp

        Returns:
            datetime: 정규화된 datetime 객체
        """
        if isinstance(date_value, str):
            return datetime.strptime(date_value, '%Y-%m-%d')
        elif isinstance(date_value, date) and not isinstance(date_value, datetime):
            return datetime.combine(date_value, datetime.min.time())
        elif isinstance(date_value, pd.Timestamp):
            return date_value.to_pydatetime()
        else:
            # 이미 datetime 객체
            return date_value

    @staticmethod
    def _remove_timezone(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
        """
        DatetimeIndex에서 타임존을 제거합니다.

        Args:
            index: pandas DatetimeIndex

        Returns:
            pd.DatetimeIndex: 타임존이 제거된 인덱스

        Note:
            한국 주식(Asia/Seoul)과 환율(UTC) 간 타임존 불일치 해결
        """
        if index.tz is not None:
            return index.tz_localize(None)
        return index

    async def load_and_prepare_exchange_rates(
        self,
        currency: str,
        start_date,
        end_date,
        target_date_range: Optional[pd.DatetimeIndex] = None,
        buffer_days: int = TradingThresholds.EXCHANGE_RATE_BUFFER_DAYS
    ) -> pd.DataFrame:
        """
        환율 데이터를 로딩하고 전처리합니다.

        Args:
            currency: 통화 코드 (KRW, JPY, EUR, etc.)
            start_date: 시작 날짜 (str, date, datetime)
            end_date: 종료 날짜 (str, date, datetime)
            target_date_range: reindex할 대상 날짜 범위 (None이면 생성)
            buffer_days: 시작일 이전 버퍼 일수 (기본 60일)

        Returns:
            pd.DataFrame: 전처리된 환율 데이터 (Close 컬럼 포함)

        Raises:
            ValueError: 지원하지 않는 통화이거나 환율 데이터가 없는 경우

        Note:
            - buffer_days만큼 시작일을 앞당겨서 데이터 로딩
            - 타임존 제거 후 forward-fill, backward-fill 적용
            - target_date_range와 정렬하여 누락 날짜 보정
        """
        # USD는 변환 불필요
        if currency == 'USD':
            raise ValueError("USD는 환율 변환이 필요하지 않습니다")

        # 지원 통화 확인
        if currency not in SUPPORTED_CURRENCIES:
            raise ValueError(f"지원하지 않는 통화: {currency}")

        exchange_ticker = SUPPORTED_CURRENCIES[currency]
        if not exchange_ticker:
            raise ValueError(f"{currency} 환율 티커가 정의되지 않았습니다")

        # 날짜 정규화
        start_date_obj = self._normalize_date_to_datetime(start_date)

        # 버퍼 추가 (과거 데이터 확보)
        exchange_start_date_obj = start_date_obj - timedelta(days=buffer_days)
        exchange_start_date = exchange_start_date_obj.strftime('%Y-%m-%d')

        logger.info(f"{currency} 환율 데이터 로드 중: {exchange_ticker} ({exchange_start_date} ~ {end_date})")

        # 환율 데이터 로딩 (asyncio.to_thread로 async/sync 경계 준수)
        exchange_data = await asyncio.to_thread(
            load_ticker_data, exchange_ticker, exchange_start_date, end_date
        )

        if exchange_data is None or exchange_data.empty:
            raise ValueError(f"{currency} 환율 데이터를 로드할 수 없습니다")

        # 타임존 제거 (한국 주식 vs 환율 데이터 타임존 불일치 해결)
        exchange_data.index = self._remove_timezone(exchange_data.index)

        # target_date_range와 정렬 (forward-fill + backward-fill)
        if target_date_range is not None:
            target_index_no_tz = self._remove_timezone(target_date_range)
            exchange_data = exchange_data.reindex(target_index_no_tz, method='ffill')
            exchange_data = exchange_data.bfill()

        logger.info(f"환율 데이터 전처리 완료: {len(exchange_data)}일치")
        return exchange_data

    async def convert_dataframe_to_usd(
        self,
        ticker: str,
        data: pd.DataFrame,
        start_date,
        end_date,
        currency: Optional[str] = None
    ) -> pd.DataFrame:
        """
        주가 DataFrame을 원래 통화에서 USD로 변환합니다.

        Args:
            ticker: 종목 심볼 (currency 추론용)
            data: 가격 데이터 (Open, High, Low, Close, Volume 컬럼)
            start_date: 시작 날짜
            end_date: 종료 날짜
            currency: 통화 코드 (None이면 DB에서 조회)

        Returns:
            pd.DataFrame: USD로 변환된 가격 데이터

        Note:
            - USD 통화인 경우 원본 데이터를 그대로 반환
            - 변환 실패 시 경고 로그와 함께 원본 데이터 반환
            - Open, High, Low, Close 컬럼에만 변환 적용
        """
        # 통화 정보 조회
        if currency is None:
            try:
                ticker_info = await asyncio.to_thread(get_ticker_info_from_db, ticker)
                currency = ticker_info.get('currency', 'USD')
                logger.info(f"{ticker} 통화: {currency}")
            except Exception as e:
                logger.warning(f"{ticker} 통화 정보 조회 실패: {e}, USD로 가정")
                currency = 'USD'

        # USD면 변환 불필요
        if currency == 'USD':
            return data

        # 지원하지 않는 통화는 경고 후 원본 반환
        if currency not in SUPPORTED_CURRENCIES:
            logger.warning(f"지원하지 않는 통화: {currency}, 변환 없이 진행")
            return data

        try:
            # 환율 데이터 로딩 및 전처리
            exchange_data = await self.load_and_prepare_exchange_rates(
                currency=currency,
                start_date=start_date,
                end_date=end_date,
                target_date_range=data.index,
                buffer_days=TradingThresholds.EXCHANGE_RATE_BUFFER_DAYS
            )

            # 환율 데이터 요약 로깅
            if not exchange_data.empty:
                rate_min = exchange_data['Close'].min()
                rate_max = exchange_data['Close'].max()
                rate_mean = exchange_data['Close'].mean()
                logger.info(
                    f"{ticker} 환율 데이터 로드 완료: {len(exchange_data)} 포인트, "
                    f"환율 범위 {rate_min:.4f} ~ {rate_max:.4f} (평균 {rate_mean:.4f})"
                )

            # 가격 데이터 복사
            converted_data = data.copy()

            # 변환 전 가격 범위
            original_close_min = data['Close'].min()
            original_close_max = data['Close'].max()

            # 각 행에 대해 환율 적용
            converted_count = 0
            for idx in converted_data.index:
                # 타임존 제거 (환율 데이터 인덱스와 매칭)
                idx_no_tz = self._remove_timezone(pd.DatetimeIndex([idx]))[0]

                # 환율 데이터에서 해당 날짜의 환율 가져오기
                if idx_no_tz in exchange_data.index and pd.notna(exchange_data.loc[idx_no_tz, 'Close']):
                    exchange_rate = exchange_data.loc[idx_no_tz, 'Close']

                    # 통화별 변환 비율 계산
                    multiplier = self.get_conversion_multiplier(currency, exchange_rate)

                    # OHLC 컬럼 변환
                    for col in ['Open', 'High', 'Low', 'Close']:
                        if col in converted_data.columns:
                            converted_data.loc[idx, col] *= multiplier

                    converted_count += 1

            # 변환 후 가격 범위
            converted_close_min = converted_data['Close'].min()
            converted_close_max = converted_data['Close'].max()

            logger.info(
                f"{ticker} 가격을 {currency}에서 USD로 변환 완료: "
                f"{converted_count}/{len(data)} 포인트 변환됨, "
                f"Close 범위 {original_close_min:.2f}~{original_close_max:.2f} {currency} → "
                f"{converted_close_min:.2f}~{converted_close_max:.2f} USD"
            )
            return converted_data

        except Exception as e:
            logger.error(f"통화 변환 중 오류: {e}, 원본 데이터 사용")
            return data

    async def load_multiple_exchange_rates(
        self,
        currencies: list[str],
        start_date,
        end_date,
        date_range: pd.DatetimeIndex,
        buffer_multiplier: int = 2
    ) -> Dict[str, Dict[date, float]]:
        """
        여러 통화의 환율을 한번에 로딩합니다 (포트폴리오용).

        Args:
            currencies: 통화 코드 리스트 (예: ['KRW', 'JPY', 'EUR'])
            start_date: 시작 날짜
            end_date: 종료 날짜
            date_range: 전체 날짜 범위 (reindex용)
            buffer_multiplier: buffer 일수 배수 (기본 2배)

        Returns:
            Dict[str, Dict[date, float]]: 통화별 날짜-환율 매핑
            예: {'KRW': {date(2023,1,1): 1300.5, ...}, 'JPY': {...}}

        Note:
            - USD는 자동으로 제외
            - 날짜를 key로 하는 dict로 변환하여 O(1) 조회 성능 보장
            - 환율 데이터 로드 실패 시 해당 통화는 제외하고 계속 진행
        """
        exchange_rates_by_currency: Dict[str, Dict[date, float]] = {}

        # 날짜 정규화
        start_date_obj = self._normalize_date_to_datetime(start_date)

        # 버퍼 추가
        buffer_days = EXCHANGE_RATE_LOOKBACK_DAYS * buffer_multiplier
        exchange_start_date_obj = start_date_obj - timedelta(days=buffer_days)
        exchange_start_date = exchange_start_date_obj.strftime('%Y-%m-%d')

        for currency in currencies:
            # USD는 변환 불필요
            if currency == 'USD':
                continue

            # 지원하지 않는 통화 건너뛰기
            if currency not in SUPPORTED_CURRENCIES:
                logger.warning(f"지원하지 않는 통화 건너뛰기: {currency}")
                continue

            exchange_ticker = SUPPORTED_CURRENCIES[currency]
            if not exchange_ticker:
                continue

            try:
                logger.info(f"{currency} 환율 데이터 로드 중: {exchange_ticker}")

                # 환율 데이터 로딩
                exchange_data = await asyncio.to_thread(
                    load_ticker_data, exchange_ticker, exchange_start_date, end_date
                )

                if exchange_data is None or exchange_data.empty:
                    logger.warning(f"{currency} 환율 데이터 없음, 건너뛰기")
                    continue

                # 타임존 제거 및 reindex
                exchange_data.index = self._remove_timezone(exchange_data.index)
                date_range_no_tz = self._remove_timezone(date_range)
                exchange_data = exchange_data.reindex(date_range_no_tz, method='ffill')
                exchange_data = exchange_data.bfill()

                # date-keyed dict로 변환 (O(1) 조회)
                currency_rates: Dict[date, float] = {}
                for date_idx, row in exchange_data.iterrows():
                    if pd.notna(row['Close']):
                        # datetime을 date로 변환
                        if hasattr(date_idx, 'date'):
                            currency_rates[date_idx.date()] = float(row['Close'])
                        else:
                            currency_rates[date_idx] = float(row['Close'])

                exchange_rates_by_currency[currency] = currency_rates
                logger.info(f"{currency} 환율 {len(currency_rates)}일치 로드 완료")

            except Exception as e:
                logger.warning(f"{currency} 환율 로드 실패: {e}, 건너뛰기")
                continue

        return exchange_rates_by_currency


# 전역 인스턴스
currency_converter = CurrencyConverter()
