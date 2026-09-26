"""시뮬레이션용 시장 데이터 사전 정렬 (가격·환율·거래 가능 마스크)

PortfolioSimulationEngine의 일별 루프가 매일 O(1)로 조회할 수 있도록, 시뮬레이션
기간 전체의 가격(USD 환산)과 "그날 RAW 데이터가 실제로 있었는가" 마스크를 미리
date_range에 맞춰 둔다. 루프 상태(보유 수량·현금·상장폐지)는 다루지 않는다.

엔진의 같은 이름 메서드(`_pre_calculate_prices` 등)는 이 함수들에 위임한다 —
테스트와 취소 체크포인트 검증이 엔진 메서드를 직접 호출하거나 바꿔 끼운다.
"""
from datetime import date
from typing import Dict, Set, Tuple

import pandas as pd

from app.domain.portfolio_domain import DcaStrategyInfo


def pre_calculate_prices(
    date_range: pd.DatetimeIndex,
    stock_amounts: Dict[str, float],
    portfolio_data: Dict[str, pd.DataFrame],
    dca_info: Dict[str, DcaStrategyInfo],
    ticker_currencies: Dict[str, str],
    exchange_rates_by_currency: Dict[str, Dict[date, float]]
) -> Tuple[Dict[str, pd.Series], Dict[str, pd.Series]]:
    """
    [성능 최적화] 시뮬레이션 기간 동안의 모든 가격 데이터를 미리 정렬(Pre-align) 및 계산합니다.

    기존 로직(매일 슬라이싱)의 O(N^2) 복잡도를 O(N)으로 줄이기 위해 사용됩니다.
    - 각 종목의 데이터를 date_range에 맞춰 Reindex
    - Forward Fill로 결측치(휴장일 등) 채움
    - 환율 변환 미리 적용 (가능한 경우)

    Returns:
        aligned_prices: {ticker: Series(adjusted_price, index=date_range)}
        aligned_exchange_rates: {currency: Series(rate, index=date_range)}
    """
    aligned_prices = {}
    aligned_exchange_rates = {}

    # 1. 환율 데이터 정렬
    # (통화별로 미리 Series 생성)
    for currency, rates_map in exchange_rates_by_currency.items():
        if not rates_map:
            continue
        # date -> datetime64 변환을 위해 DataFrame/Series 생성
        rates_series = pd.Series(rates_map)
        rates_series.index = pd.to_datetime(rates_series.index)

        # Reindex & FFill
        # [Copilot Suggestion] ffill만 하면 시뮬레이션 시작일보다 환율 데이터가 늦게 시작될 경우 앞부분이 NaN이 됨.
        # bfill을 추가하여 앞부분 결측치도 보완 (최초 환율로 메꿈)
        aligned_rate = rates_series.reindex(date_range).ffill().bfill()
        aligned_exchange_rates[currency] = aligned_rate

    # 2. 주가 데이터 정렬 & 환율 적용
    for unique_key in stock_amounts.keys():
        symbol = dca_info[unique_key].symbol
        if symbol not in portfolio_data:
            continue

        df = portfolio_data[symbol]
        # 인덱스가 이미 datetime이어야 함
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Close 가격만 추출 및 정렬
        price_series = df['Close'].reindex(date_range).ffill()

        # 환율 변환
        currency = ticker_currencies.get(unique_key, 'USD')
        if currency != 'USD' and currency in aligned_exchange_rates:
            # 벡터 연산으로 전체 기간 환율 적용
            # [Copilot Suggestion] 벡터 연산 (환율 적용) - apply 제거 및 Vectorization 적용
            exchange_rates = aligned_exchange_rates[currency]

            # 주요 통화(EUR, GBP 등)는 직접 곱하기, 그 외(KRW, JPY 등)는 나누기 역수
            # CurrencyConverter.get_conversion_multiplier 로직을 벡터화
            if currency in ['EUR', 'GBP', 'AUD', 'CAD', 'CHF']:
                 # Direct multiplication
                 price_series = price_series * exchange_rates
            else:
                 # Inverse (1 / rate)
                 # 0 또는 NaN인 경우 1.0으로 처리 (Division by Zero 방지)
                 valid_mask = (exchange_rates > 0) & (pd.notnull(exchange_rates))
                 multipliers = pd.Series(1.0, index=exchange_rates.index)
                 multipliers[valid_mask] = 1.0 / exchange_rates[valid_mask]

                 price_series = price_series * multipliers
        elif currency != 'USD':
            # [P2-02] 환율 데이터가 없다고 원본(비USD) 가격을 그대로 흘려보내면
            # 안 된다 -- 이후 시뮬레이션이 이 가격을 USD 현금과 그대로 합산해,
            # 예컨대 KRW 7만원대 가격이 $70,000짜리 자산으로 둔갑한 채 "성공"으로
            # 보고되는 조용한 오염이 발생한다 (기존에는 경고 로그만 남기고 계속
            # 진행했음). 지원하지 않는 통화이거나 환율 데이터 로딩이 실패한
            # 경우이므로 명시적으로 실패를 알린다.
            raise ValueError(
                f"{symbol} ({unique_key}) 통화 '{currency}'의 환율 데이터가 없어 "
                f"USD로 변환할 수 없습니다 (지원하지 않는 통화이거나 환율 데이터 "
                f"로딩 실패). 변환되지 않은 원본 가격으로 백테스트를 진행할 수 없습니다."
            )

        aligned_prices[unique_key] = price_series

    return aligned_prices, aligned_exchange_rates

def get_daily_prices_from_aligned(
    current_date: pd.Timestamp,
    aligned_prices: Dict[str, pd.Series],
    aligned_exchange_rates: Dict[str, pd.Series],
    ticker_currencies: Dict[str, str],
    last_valid_exchange_rates: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    [성능 최적화] 미리 계산된 데이터에서 O(1)로 당일 가격 조회
    """
    current_prices = {}

    # 1. 환율 캐시 업데이트
    for currency, rates_series in aligned_exchange_rates.items():
        try:
            rate = rates_series.at[current_date]
            if pd.notnull(rate):
                last_valid_exchange_rates[currency] = rate
        except KeyError:
            pass # 해당 통화의 환율 데이터가 없는 날짜는 캐시 갱신 없이 진행

    # 2. 가격 조회
    for unique_key, price_series in aligned_prices.items():
        try:
            price = price_series.at[current_date]
            # NaN 체크 (해당 날짜 데이터 없음 or 상장폐지 등)
            if pd.notnull(price):
                current_prices[unique_key] = float(price)
        except KeyError:
            pass # 배열에 해당 날짜 데이터가 없으면 스킵 (상장폐지, 휴장일 등)

    return current_prices, last_valid_exchange_rates

def pre_calculate_tradeable_mask(
    date_range: pd.DatetimeIndex,
    stock_amounts: Dict[str, float],
    portfolio_data: Dict[str, pd.DataFrame],
    dca_info: Dict[str, DcaStrategyInfo]
) -> Dict[str, pd.Series]:
    """
    [P2-14] 종목별로 "해당 날짜에 실제로 RAW 데이터가 존재했는가"를 나타내는
    불리언 마스크를 date_range에 맞춰 미리 계산합니다.

    `_pre_calculate_prices`가 만드는 aligned_prices는 밸류에이션을 위해
    ffill로 결측치를 채운 시리즈이므로, 그 자체로는 "그 날짜에 실제로 거래가
    가능했는가"를 답할 수 없다 (ffill은 무한정 이전 값을 반복하기 때문에,
    상장폐지된 종목도 영원히 값을 갖는 것처럼 보인다). 이 메서드는 reindex
    직전의 RAW 인덱스만을 근거로 마스크를 만들어, 거래 실행(초기 매수/DCA
    정기 매수/리밸런싱)과 상장폐지 감지가 밸류에이션과 별개로 "실제로 관측된
    날"만 참조하도록 한다.

    `_pre_calculate_prices`와 정확히 같은 (date_range, stock_amounts,
    portfolio_data, dca_info) 조합에 대해 계산되므로, 함께 사용해도 두
    딕셔너리의 key 집합은 항상 일치한다 (같은 이유로 심볼이 없으면 둘 다
    해당 unique_key를 건너뛴다).

    Returns:
        {unique_key: Series(bool, index=date_range)} -- True인 날짜만 그
        종목의 원본 Close 데이터가 실제로 존재했던(관측된) 날이다.
    """
    aligned_tradeable: Dict[str, pd.Series] = {}

    for unique_key in stock_amounts.keys():
        symbol = dca_info[unique_key].symbol
        if symbol not in portfolio_data:
            continue

        df = portfolio_data[symbol]
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        observed = df['Close'].notna()
        aligned_tradeable[unique_key] = observed.reindex(date_range, fill_value=False)

    return aligned_tradeable

def get_daily_tradeable_keys(
    current_date: pd.Timestamp,
    aligned_tradeable: Dict[str, pd.Series]
) -> Set[str]:
    """
    [P2-14] 미리 계산된 tradeable 마스크에서 O(1)로 당일 관측 여부를 조회합니다.

    Returns:
        오늘 RAW 데이터로 실제 관측된 unique_key 집합.
    """
    tradeable_today: Set[str] = set()
    for unique_key, mask_series in aligned_tradeable.items():
        try:
            if bool(mask_series.at[current_date]):
                tradeable_today.add(unique_key)
        except KeyError:
            pass  # 마스크에 해당 날짜가 없으면 관측되지 않은 것으로 취급
    return tradeable_today
