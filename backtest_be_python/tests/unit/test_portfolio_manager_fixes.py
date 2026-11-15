"""
PortfolioManagerService 재무 정확성 버그 수정 회귀 테스트

**테스트 범위**:
- BUG P1-03 (weight-mode denominator): weight만 입력된 포트폴리오에서
  total_amount를 하드코딩된 100.0으로 계산하면, 스키마가 허용하는
  95~105% 비중 합계 범위에서 실제 투자 원금과 다른 값을 분모로 사용하게 되어
  변동 없는(flat) 시장에서도 포트폴리오 수익률이 왜곡되어 보고됨
  (예: 비중 합계 95% -> flat 시장인데도 -5%로 보고).
- BUG P1-05 (commission dropped): 개별 종목 백테스트 요청(BacktestRequest)을
  생성할 때 포트폴리오 요청의 commission이 전달되지 않아, 사용자가 지정한
  수수료(예: 0.03) 대신 스키마 기본값(0.002)이 조용히 사용됨.

각 버그는 먼저 실패하는 테스트(RED)로 재현한 뒤 구현을 수정해 통과(GREEN)
시키는 TDD 절차를 따른다. backtest_service.run_backtest()는 외부 I/O
(데이터 로딩, backtesting.py 실행)를 수행하므로 AsyncMock으로 격리한다.
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.schemas.schemas import PortfolioBacktestRequest
from app.services.portfolio_manager_service import PortfolioManagerService

pytestmark = pytest.mark.unit


def _flat_market_result(backtest_req):
    """개별 종목 백테스트 결과를 흉내내는 flat 시장 결과 (수익률 0%).

    final_equity를 요청받은 initial_cash와 동일하게 반환하여,
    "가격 변동이 전혀 없는 시장"을 시뮬레이션한다.
    run_strategy_portfolio_backtest가 result.__dict__를 strategy_stats로
    사용하므로 SimpleNamespace를 사용해 실제 BacktestResult와 유사한
    속성 접근(.final_equity, getattr(..., 'total_trades', 0) 등)을 지원한다.
    """
    return SimpleNamespace(
        final_equity=backtest_req.initial_cash,
        total_trades=0,
        win_rate_pct=0.0,
        max_drawdown_pct=0.0,
        sharpe_ratio=0.0,
    )


@pytest.fixture
def service():
    """검증 대상 서비스의 격리된 인스턴스"""
    return PortfolioManagerService()


@pytest.mark.asyncio
class TestWeightModeDenominator:
    """P1-03: weight-only 포트폴리오의 total_amount 계산 검증

    app/services/portfolio_manager_service.py의
    run_strategy_portfolio_backtest()에서 weight만 입력된 경우
    total_amount = sum(amounts.values())로 계산되어야 하며,
    하드코딩된 100.0을 분모로 사용해서는 안 된다.
    """

    async def test_weights_summing_to_95_report_zero_return_on_flat_market(self, service):
        """
        Given: weight=50, weight=45 (합계 95%, 스키마가 허용하는 95~105% 범위
               내)로만 구성되고 amount는 입력하지 않은 포트폴리오
        When: 두 종목 모두 가격 변동이 없는(flat) 시장에서 전략 백테스트가
              실행됨 (각 종목의 final_equity == initial_cash)
        Then: 실제 투자 원금(50+45=95)과 최종 가치(95)가 동일하므로
              포트폴리오 총 수익률은 0%에 가까워야 한다.
              하드코딩된 100 분모를 사용하면 (95/100 - 1) * 100 = -5.0%로
              잘못 계산된다.
        """
        request = PortfolioBacktestRequest(
            portfolio=[
                {"symbol": "AAA", "weight": 50},
                {"symbol": "BBB", "weight": 45},
            ],
            start_date="2023-01-01",
            end_date="2023-06-01",
            strategy="sma_strategy",
        )

        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=AsyncMock(side_effect=_flat_market_result),
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result["status"] == "success", result.get("error")

        portfolio_return = result["data"]["portfolio_statistics"]["Total_Return"]
        assert portfolio_return == pytest.approx(0.0, abs=1e-6), (
            f"weight 합계가 95%일 때 flat 시장에서는 수익률이 0%여야 하는데 "
            f"{portfolio_return}로 계산됨 (하드코딩된 100 분모 버그 의심)"
        )

        # 'portfolio_result' 블록도 동일한 portfolio_return 값을 공유해야 함
        assert result["data"]["portfolio_result"]["total_return_pct"] == pytest.approx(
            0.0, abs=1e-6
        )

    async def test_amount_mode_is_unaffected(self, service):
        """
        Given: amount만 입력된 포트폴리오 (weight 모드가 아님)
        When: flat 시장에서 백테스트 실행
        Then: amount 모드는 애초에 total_amount = sum(amounts)이므로
              기존과 동일하게 수익률이 0%로 나와야 한다 (회귀 방지).
        """
        request = PortfolioBacktestRequest(
            portfolio=[
                {"symbol": "AAA", "amount": 6000.0},
                {"symbol": "BBB", "amount": 4000.0},
            ],
            start_date="2023-01-01",
            end_date="2023-06-01",
            strategy="sma_strategy",
        )

        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=AsyncMock(side_effect=_flat_market_result),
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result["status"] == "success", result.get("error")
        portfolio_return = result["data"]["portfolio_statistics"]["Total_Return"]
        assert portfolio_return == pytest.approx(0.0, abs=1e-6)


@pytest.mark.asyncio
class TestCommissionPropagation:
    """P1-05: 개별 종목 BacktestRequest에 포트폴리오 commission이 전달되는지 검증

    app/services/portfolio_manager_service.py의
    run_strategy_portfolio_backtest()가 생성하는 BacktestRequest는
    request.commission을 명시적으로 전달해야 하며, 그렇지 않으면
    BacktestRequest 스키마 기본값(0.002)이 조용히 사용된다.
    """

    async def test_portfolio_commission_is_passed_to_individual_backtest_request(
        self, service
    ):
        """
        Given: commission=0.03로 설정된 amount 모드 단일 종목 포트폴리오
               (스키마 기본값 0.002와 다른 값)
        When: 개별 종목 백테스트 요청(BacktestRequest)이 생성되어
              backtest_service.run_backtest()에 전달됨
        Then: 전달된 BacktestRequest.commission은 0.002(기본값)가 아니라
              포트폴리오 요청의 commission인 0.03이어야 한다.
        """
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAA", "amount": 1000.0}],
            start_date="2023-01-01",
            end_date="2023-06-01",
            strategy="sma_strategy",
            commission=0.03,
        )

        mock_run_backtest = AsyncMock(side_effect=_flat_market_result)
        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=mock_run_backtest,
        ):
            result = await service.run_strategy_portfolio_backtest(request)

        assert result["status"] == "success", result.get("error")
        mock_run_backtest.assert_awaited_once()

        called_request = mock_run_backtest.call_args.args[0]
        assert called_request.commission == pytest.approx(0.03), (
            "개별 종목 BacktestRequest에 포트폴리오 요청의 commission이 "
            "전달되지 않고 스키마 기본값이 사용됨"
        )

    async def test_default_commission_is_still_respected(self, service):
        """
        Given: commission을 명시하지 않은 포트폴리오 요청 (기본값 0.002 사용)
        When: 개별 종목 백테스트 요청이 생성됨
        Then: BacktestRequest.commission은 request.commission(기본값 0.002)과
              일치해야 한다 (명시적 전달이 기본값 흐름도 깨지 않는지 확인).
        """
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAA", "amount": 1000.0}],
            start_date="2023-01-01",
            end_date="2023-06-01",
            strategy="sma_strategy",
        )
        assert request.commission == 0.002  # 스키마 기본값 전제 확인

        mock_run_backtest = AsyncMock(side_effect=_flat_market_result)
        with patch(
            "app.services.portfolio_manager_service.backtest_service.run_backtest",
            new=mock_run_backtest,
        ):
            await service.run_strategy_portfolio_backtest(request)

        called_request = mock_run_backtest.call_args.args[0]
        assert called_request.commission == pytest.approx(0.002)
