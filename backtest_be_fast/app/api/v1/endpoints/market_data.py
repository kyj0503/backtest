"""Reference market data, independently retriable without another simulation."""
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


class MarketDataQuery(BaseModel):
    model_config = {'extra': 'forbid'}
    symbols: list[str] = Field(default_factory=list, max_length=settings.max_portfolio_items)
    start_date: date
    end_date: date
    include_stock_data: bool = True
    include_volatility_events: bool = True
    include_exchange_rates: bool = True
    include_benchmarks: bool = True
    include_news: bool = True

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, values):
        return list(dict.fromkeys(PortfolioStock(symbol=value).symbol for value in values))

    @model_validator(mode='after')
    def validate_dates(self):
        if self.end_date < self.start_date:
            raise ValueError('종료일은 시작일 이후여야 합니다.')
        if self.end_date > date.today():
            raise ValueError('미래 날짜는 조회할 수 없습니다.')
        if (self.end_date - self.start_date).days > settings.max_backtest_duration_days:
            raise ValueError('조회 기간이 최대 허용 기간을 초과했습니다.')
        return self


@lru_cache(maxsize=1)
def get_market_data_runner():
    return BacktestJobRunner(
        slot_dir=settings.backtest_slot_dir + '-market-data',
        max_concurrent=settings.max_concurrent_market_data,
        per_client=1,
        queue_timeout=settings.market_data_queue_timeout_seconds,
        exec_timeout=settings.market_data_timeout_seconds,
        cancel_grace=settings.backtest_cancel_grace_seconds,
        running_metric=_running,
        waiting_metric=_waiting,
        job_name='참고 데이터 조회',
    )


@router.get('', summary='주가·환율·벤치마크·뉴스 조회')
async def get_market_data(query: Annotated[MarketDataQuery, Query()], request: Request):
    async def collect():
        data = await asyncio.to_thread(
            unified_data_service.collect_all_unified_data,
            symbols=query.symbols,
            start_date=query.start_date.isoformat(),
            end_date=query.end_date.isoformat(),
            include_news=query.include_news,
            news_display_count=15,
            include_stock_data=query.include_stock_data,
            include_volatility_events=query.include_volatility_events,
            include_exchange_rates=query.include_exchange_rates,
            include_benchmarks=query.include_benchmarks,
            timeout_seconds=settings.supplemental_data_timeout_seconds,
        )
        benchmark = data.get('sp500_benchmark', [])
        data['sp500_total_return_pct'] = (
            unified_data_service.calculate_benchmark_return(benchmark)
            if len(benchmark) >= 2 else None
        )
        return {'status': 'success', 'data': recursive_serialize(data)}

    try:
        return await get_market_data_runner().run(
            collect, client_key=_client_key(request),
            is_disconnected=request.is_disconnected, label='market-data',
        )
    except BacktestRejected as exc:
        return _rejection_response(exc)
