"""Independently retriable reads sharing one bounded reference-data capacity."""
import asyncio
from datetime import date
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Query, Request
from prometheus_client import Gauge
from pydantic import BaseModel, Field, field_validator, model_validator

from ....core.config import settings
from ....schemas.schemas import PortfolioStock
from ....services.backtest_runner import BacktestJobRunner, BacktestRejected
from ....services.unified_data_service import unified_data_service
from ....utils.serializers import recursive_serialize
from .backtest import _client_key, _rejection_response

router = APIRouter()
_running = Gauge('market_data_jobs_running', 'Active reference-data jobs', multiprocess_mode='livesum')
_waiting = Gauge('market_data_jobs_waiting', 'Queued reference-data jobs', multiprocess_mode='livesum')

# Both price views share one fetch. A response can only update its own fields.
READ_FIELDS = {
    'prices': ('ticker_info', 'stock_data', 'volatility_events'),
    'exchange-rates': ('exchange_rates', 'exchange_stats'),
    'benchmarks': ('sp500_benchmark', 'nasdaq_benchmark'),
    'news': ('latest_news',),
}
READ_STATUSES = {
    'prices': ('ticker_info', 'stock_data', 'volatility_events'),
    'exchange-rates': ('exchange_rates',),
    'benchmarks': ('benchmarks',),
    'news': ('news',),
}


class SymbolsQuery(BaseModel):
    model_config = {'extra': 'forbid'}
    symbols: list[str] = Field(min_length=1, max_length=settings.max_portfolio_items)

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, values):
        return list(dict.fromkeys(PortfolioStock(symbol=value).symbol for value in values))


class PeriodQuery(BaseModel):
    model_config = {'extra': 'forbid'}
    start_date: date
    end_date: date

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError('종료일은 시작일 이후여야 합니다.')
        if self.end_date > date.today():
            raise ValueError('미래 날짜는 조회할 수 없습니다.')
        if (self.end_date - self.start_date).days > settings.max_backtest_duration_days:
            raise ValueError('조회 기간이 최대 허용 기간을 초과했습니다.')
        return self


class PricesQuery(PeriodQuery, SymbolsQuery):
    pass


class NewsQuery(SymbolsQuery):
    limit: int = Field(default=15, ge=1, le=20)


@lru_cache(maxsize=1)
def get_market_data_runner():
    return BacktestJobRunner(
        slot_dir=settings.backtest_slot_dir + '-market-data',
        max_concurrent=settings.max_concurrent_market_data,
        per_client=4,
        queue_timeout=settings.market_data_queue_timeout_seconds,
        exec_timeout=settings.market_data_timeout_seconds,
        cancel_grace=settings.backtest_cancel_grace_seconds,
        running_metric=_running, waiting_metric=_waiting, job_name='참고 데이터 조회',
    )


async def _read(section: str, request: Request, *, symbols=None, start_date=None, end_date=None, limit=15):
    async def collect():
        data = await asyncio.to_thread(
            unified_data_service.collect_all_unified_data,
            symbols=symbols or [],
            start_date=start_date.isoformat() if start_date else None,
            end_date=end_date.isoformat() if end_date else None,
            include_ticker_info=section == 'prices',
            include_stock_data=section == 'prices',
            include_volatility_events=section == 'prices',
            include_exchange_rates=section == 'exchange-rates',
            include_benchmarks=section == 'benchmarks',
            include_news=section == 'news',
            news_display_count=limit,
            timeout_seconds=settings.supplemental_data_timeout_seconds,
        )
        result = {field: data[field] for field in READ_FIELDS[section]}
        result['supplemental_status'] = {
            name: data['supplemental_status'][name] for name in READ_STATUSES[section]
        }
        if section == 'benchmarks':
            benchmark = result['sp500_benchmark']
            result['sp500_total_return_pct'] = (
                unified_data_service.calculate_benchmark_return(benchmark)
                if len(benchmark) >= 2 else None
            )
        return {'status': 'success', 'data': recursive_serialize(result)}

    try:
        return await get_market_data_runner().run(
            collect, client_key=_client_key(request), is_disconnected=request.is_disconnected,
            label=section,
        )
    except BacktestRejected as exc:
        return _rejection_response(exc)


@router.get('/prices', summary='종목 정보·주가·급등락 이벤트 조회')
async def get_prices(query: Annotated[PricesQuery, Query()], request: Request):
    return await _read('prices', request, symbols=query.symbols,
                       start_date=query.start_date, end_date=query.end_date)


@router.get('/exchange-rates', summary='기간별 원달러 환율·통계 조회')
async def get_exchange_rates(query: Annotated[PeriodQuery, Query()], request: Request):
    return await _read('exchange-rates', request, start_date=query.start_date, end_date=query.end_date)


@router.get('/benchmarks', summary='기간별 S&P 500·NASDAQ 조회')
async def get_benchmarks(query: Annotated[PeriodQuery, Query()], request: Request):
    return await _read('benchmarks', request, start_date=query.start_date, end_date=query.end_date)


@router.get('/news', summary='종목별 최신 뉴스 조회 — 백테스트 기간과 무관')
async def get_news(query: Annotated[NewsQuery, Query()], request: Request):
    return await _read('news', request, symbols=query.symbols, limit=query.limit)
