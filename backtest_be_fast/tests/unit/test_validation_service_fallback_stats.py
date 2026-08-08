"""ValidationService.create_fallback_stats 조작된 필드 제거 회귀 테스트 (P3-21b)

버그: create_fallback_stats()는 실제로 백테스팅 엔진이 시뮬레이션하지 않은
거래를 마치 일어난 것처럼 '# Trades': 1 / 'Win Rate [%]': 100.0(또는 0.0)으로
꾸며서 반환했다. 또한 일간 수익률의 표준편차를 연환산 없이 그대로
'Volatility [%]' 키(실제 backtesting.py 경로 및 이 앱의 응답 스키마에서
연환산 변동성으로 취급되는 키 — 실제 backtesting._stats.compute_stats도 동일한
개념을 'Volatility (Ann.) [%]'라는 이름으로 연환산해서 채운다)에 채워 넣어,
값의 자릿수/스케일이 실제 경로와 어긋났다.

도달성 메모: app/services/backtest_engine.py의 두 호출부
(run_backtest()의 '결과 무효' 분기, _convert_result_to_response()의 예외
핸들러)를 이번 배치에서 raise로 바꿔 이 메서드의 유일한 실서비스 호출 경로를
제거했다. 다만 _create_fallback_result()는 tests/unit/test_backtest_engine.py
(이번 작업 범위 밖, 편집 불가)가 mocked validation_service로 직접 호출하는
계약을 갖고 있어 삭제할 수 없고, 그 메서드 본문은 실제 ValidationService를
계속 참조한다. 따라서 create_fallback_stats를 통째로 지우면
(_create_fallback_result가 실제 서비스와 함께 호출될 경우) AttributeError를
숨기는 죽은 참조만 남기게 되므로, 메서드 자체는 남기고 조작된 필드만 정직한
값으로 고친다.

수정 후: 거래 관련 지표는 정직하게 0/0.0을 반환하고(실제 거래가 없었으므로),
변동성은 연환산(252 거래일 기준 sqrt(252) 스케일링)되어 반환된다.
"""
import numpy as np
import pandas as pd
import pytest

from app.services.validation_service import ValidationService


pytestmark = pytest.mark.unit


@pytest.fixture
def service():
    return ValidationService()


@pytest.fixture
def rising_price_data():
    dates = pd.date_range('2023-01-01', periods=30, freq='D')
    prices = np.linspace(100, 130, 30)
    return pd.DataFrame({'Close': prices}, index=dates)


class TestNoFabricatedTradeStats:
    def test_trade_count_is_honestly_zero_not_fabricated_one(self, service, rising_price_data):
        """실제로 시뮬레이션된 거래가 없으므로 '# Trades'는 0이어야 한다
        (이전에는 조작된 값 1을 반환했다)."""
        stats = service.create_fallback_stats(rising_price_data, 10000.0)

        assert stats['# Trades'] == 0

    def test_win_rate_is_not_fabricated_when_return_is_positive(self, service, rising_price_data):
        """이전에는 상승장에서 'Win Rate [%]'를 100.0으로 꾸몄다 (실제 거래가
        없었는데도 '승리'로 표시). 거래가 없으므로 승률도 0이어야 한다."""
        stats = service.create_fallback_stats(rising_price_data, 10000.0)

        assert stats['Win Rate [%]'] == 0.0


class TestVolatilityIsAnnualized:
    def test_volatility_is_scaled_up_from_daily_std(self, service, rising_price_data):
        """'Volatility [%]' 값은 일간 표준편차를 그대로 반환하면 안 되고
        연환산되어 더 커야 한다."""
        stats = service.create_fallback_stats(rising_price_data, 10000.0)

        returns = rising_price_data['Close'].pct_change().dropna()
        daily_volatility_pct = returns.std() * 100

        assert stats['Volatility [%]'] > daily_volatility_pct

    def test_volatility_matches_sqrt_252_annualization(self, service, rising_price_data):
        """표준 연환산 계수(sqrt(252))로 스케일링된 값과 정확히 일치해야 한다."""
        stats = service.create_fallback_stats(rising_price_data, 10000.0)

        returns = rising_price_data['Close'].pct_change().dropna()
        expected = returns.std() * 100 * (252 ** 0.5)

        assert stats['Volatility [%]'] == pytest.approx(expected, rel=1e-6)


class TestGenuineBuyHoldFieldsUnaffected:
    """회귀 가드: 실제 데이터에서 계산되는 값(조작이 아닌 값)은 계속 정확해야
    한다."""

    def test_buy_and_hold_return_still_computed_from_real_prices(self, service, rising_price_data):
        stats = service.create_fallback_stats(rising_price_data, 10000.0)

        initial_price = float(rising_price_data['Close'].iloc[0])
        final_price = float(rising_price_data['Close'].iloc[-1])
        expected_return = ((final_price / initial_price) - 1) * 100

        assert stats['Return [%]'] == pytest.approx(expected_return, rel=1e-9)
        assert stats['Buy & Hold Return [%]'] == pytest.approx(expected_return, rel=1e-9)

    def test_empty_data_still_returns_safe_defaults(self, service):
        stats = service.create_fallback_stats(pd.DataFrame(), 5000.0)

        assert stats['Equity Final [$]'] == 5000.0
        assert stats['# Trades'] == 0
        assert stats['Win Rate [%]'] == 0.0
