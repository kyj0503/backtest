"""포트폴리오 데이터 로더
"""
import asyncio
import logging
import pandas as pd
from typing import Dict, List, Any, Tuple
from datetime import datetime
from app.repositories.stock_repository import StockRepository
from app.utils.currency_converter import CurrencyConverter, currency_converter as default_currency_converter

logger = logging.getLogger(__name__)

class PortfolioDataLoader:
    """
    포트폴리오 시뮬레이션에 필요한 데이터를 로드하는 역할을 담당합니다. (Data Access Facade)

    책임:
    1. Stock Data Loading: 주가 데이터 병렬 로드
    2. Metadata Loading: 티커 정보(통화 등) 배치 로드
    3. Exchange Rate Loading: 필요한 환율 데이터 로드
    """

    def __init__(
        self,
        stock_repository: StockRepository,
        currency_converter: CurrencyConverter = None
    ):
        self.stock_repository = stock_repository
        self.currency_converter = currency_converter or default_currency_converter

    async def load_stock_data_parallel(
        self,
        symbols_to_load: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 주가 데이터를 병렬로 로드합니다.
        """
        portfolio_data = {}
        if not symbols_to_load:
            return portfolio_data

        logger.info(f"포트폴리오 데이터 병렬 로드 시작: {len(symbols_to_load)}개 종목")

        load_tasks = [
            asyncio.to_thread(self.stock_repository.load_stock_data, symbol, start_date, end_date)
            for symbol in symbols_to_load
        ]

        load_results = await asyncio.gather(*load_tasks, return_exceptions=True)

        for symbol, result in zip(symbols_to_load, load_results):
            if isinstance(result, Exception):
                logger.warning(f"종목 {symbol} 데이터 로드 실패: {result}")
                continue

            if result is None or result.empty:
                logger.warning(f"종목 {symbol}의 데이터가 없습니다.")
                continue

            portfolio_data[symbol] = result
            logger.info(f"종목 {symbol} 데이터 로드 완료: {len(result)} 행")

        logger.info(f"포트폴리오 데이터 병렬 로드 완료: {len(portfolio_data)}/{len(symbols_to_load)}개 성공")
        return portfolio_data

    async def load_ticker_currencies(
        self,
        symbols: List[str]
    ) -> Dict[str, str]:
        """
        종목별 통화 정보를 배치로 조회합니다.
        key: symbol, value: currency_code
        """
        try:
            ticker_info_dict = await asyncio.to_thread(
                self.stock_repository.get_tickers_info_batch, symbols
            )
            # symbol -> currency 맵핑으로 변환
            ticker_currencies = {
                symbol: info.get('currency', 'USD')
                for symbol, info in ticker_info_dict.items()
            }
            return ticker_currencies
        except Exception as e:
            logger.warning(f"티커 정보 배치 조회 실패: {e}, 모두 USD로 가정")
            return {symbol: 'USD' for symbol in symbols}

    async def load_exchange_rates(
        self,
        currencies: List[str],
        start_date: str,
        end_date: str,
        date_range: pd.DatetimeIndex
    ) -> Dict[str, Dict]:
        """
        필요한 통화들의 환율 데이터를 로드합니다.
        """
        required_currencies = list(set(currencies) - {'USD'})
        
        if not required_currencies:
            return {}

        logger.info(f"포트폴리오 환율 로딩 시작: {len(required_currencies)}개 통화 [{', '.join(required_currencies)}]")

        exchange_rates_by_currency = await self.currency_converter.load_multiple_exchange_rates(
            currencies=required_currencies,
            start_date=start_date,
            end_date=end_date,
            date_range=date_range,
            buffer_multiplier=2
        )

        # 결과 로깅
        for currency, rates in exchange_rates_by_currency.items():
            if rates:
                rate_values = list(rates.values())
                rate_mean = sum(rate_values) / len(rate_values)
                logger.info(
                    f"환율 로드 완료 ({currency}): {len(rates)} 포인트, 평균 {rate_mean:.4f}"
                )
            else:
                logger.warning(f"환율 데이터 없음 ({currency}): 변환 불가")
                
        return exchange_rates_by_currency
