"""PortfolioSimulationEngine의 FX 변환 실패 시 계약 테스트 (P2-02)

**버그**: `_pre_calculate_prices`에서 비USD 통화인데 해당 통화의 환율 데이터가
`aligned_exchange_rates`에 없으면(예: `load_multiple_exchange_rates`가 네트워크
오류로 그 통화를 건너뛴 경우), 경고 로그만 남기고 "원본(KRW 등) 가격"을 그대로
`aligned_prices`에 채워 넣었다. 시뮬레이션은 이후 이 값을 USD인 것처럼 취급해
USD 현금과 그대로 합산하므로, 예를 들어 7만원대 KRW 주식이 $70,000짜리 자산으로
둔갑한 채 "성공"으로 보고되는 조용한 오염이 발생한다.

**수정**: 환율 데이터가 없으면 조용히 원본 가격을 쓰는 대신 예외를 발생시켜
호출자가 실패를 인지하게 한다 (currency_converter.py의 동일 패턴과 짝을 이루는
수정).
"""
import asyncio
from datetime import datetime

import pandas as pd
import pytest

from app.domain.portfolio_domain import DcaStrategyInfo
from app.services.portfolio.portfolio_simulation_engine import PortfolioSimulationEngine

pytestmark = pytest.mark.unit


def _flat_price_frame(start: str, end: str, price: float) -> pd.DataFrame:
    index = pd.bdate_range(start=start, end=end)
    return pd.DataFrame({'Close': [price] * len(index)}, index=index)


class TestPreCalculatePricesRaisesOnMissingExchangeRate:
    def test_krw_ticker_without_exchange_rate_data_raises_instead_of_using_raw_price(self):
        """RED(수정 전): KRW 종목인데 환율 데이터 로드가 실패해
        aligned_exchange_rates에 'KRW'가 없는 상황 -- 원본 7만원대 가격이 변환
        없이 그대로 쓰이면 안 된다."""
        engine = PortfolioSimulationEngine()
        date_range = pd.bdate_range(start='2024-01-01', end='2024-01-10')

        dca_info = {
            'A': DcaStrategyInfo(
                symbol='005930.KS', allocation=1.0, asset_type='stock',
                investment_type='lump_sum', monthly_amount=0.0,
            ),
        }
        # 원본 KRW 가격 (~7만원대) -- 변환되지 않은 채 새어나가면 안 되는 크기
        portfolio_data = {'005930.KS': _flat_price_frame('2024-01-01', '2024-01-10', 70000.0)}

        with pytest.raises(ValueError, match="KRW"):
            engine._pre_calculate_prices(
                date_range=date_range,
                stock_amounts={'A': 1000.0},
                portfolio_data=portfolio_data,
                dca_info=dca_info,
                ticker_currencies={'A': 'KRW'},
                exchange_rates_by_currency={},  # 환율 로드 실패를 흉내: KRW 없음
            )

    def test_execute_simulation_propagates_fx_failure_instead_of_reporting_success(self):
        """RED(수정 전): execute_simulation 전체 경로에서도 동일하게 예외가
        전파되어야 하며, 조용히 '성공'을 보고하며 미변환 가격으로 계산을
        진행하면 안 된다."""
        engine = PortfolioSimulationEngine()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 1, 10)
        date_range = pd.bdate_range(start=start, end=end)

        dca_info = {
            'A': DcaStrategyInfo(
                symbol='005930.KS', allocation=1.0, asset_type='stock',
                investment_type='lump_sum', monthly_amount=0.0,
            ),
        }
        portfolio_data = {'005930.KS': _flat_price_frame('2024-01-01', '2024-01-10', 70000.0)}

        async def _run():
            return await engine.execute_simulation(
                date_range=date_range,
                start_date_obj=start,
                end_date_obj=end,
                stock_amounts={'A': 1000.0},
                amounts={'A': 1000.0},
                cash_amount=0.0,
                total_amount=1000.0,
                portfolio_data=portfolio_data,
                dca_info=dca_info,
                ticker_currencies={'A': 'KRW'},
                exchange_rates_by_currency={},  # 환율 데이터 없음 (로드 실패 흉내)
                rebalance_frequency='none',
                commission=0.0,
            )

        with pytest.raises(ValueError):
            asyncio.run(_run())

    def test_usd_ticker_unaffected_regression_guard(self):
        """회귀 가드: USD 종목은 이 변경의 영향을 받지 않아야 한다."""
        engine = PortfolioSimulationEngine()
        date_range = pd.bdate_range(start='2024-01-01', end='2024-01-10')

        dca_info = {
            'A': DcaStrategyInfo(
                symbol='AAA', allocation=1.0, asset_type='stock',
                investment_type='lump_sum', monthly_amount=0.0,
            ),
        }
        portfolio_data = {'AAA': _flat_price_frame('2024-01-01', '2024-01-10', 100.0)}

        aligned_prices, _aligned_rates = engine._pre_calculate_prices(
            date_range=date_range,
            stock_amounts={'A': 1000.0},
            portfolio_data=portfolio_data,
            dca_info=dca_info,
            ticker_currencies={'A': 'USD'},
            exchange_rates_by_currency={},
        )

        assert (aligned_prices['A'] == 100.0).all()
