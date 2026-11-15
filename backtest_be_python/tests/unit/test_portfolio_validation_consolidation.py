"""
포트폴리오 검증 통합(P2-04) 회귀 테스트

**배경**:
app/validators/portfolio_validator.py(PortfolioValidator, 233줄)는 어디에서도
import되지 않는 죽은 코드였다 (grep으로 확인: app/validators/__init__.py와 자기
자신의 docstring 예제 외에는 참조가 전혀 없음). 그 결과 포트폴리오 백테스트
경로에는 다음 3가지 실제 버그가 있었다 (아래 각 테스트 docstring에서 pydantic
2.13으로 직접 실측한 RED 동작을 설명한다):

  1. rebalance_frequency 멤버십 검증이 없어 'nonsense' 같은 오타 값도 그대로
     통과했다. 이 값은 app/services/rebalance_helper.py::RebalanceHelper.
     is_rebalance_date()의 FREQUENCY_MAP.get(frequency)에서 None이 되어
     logger.warning()만 남기고 조용히 리밸런싱을 비활성화시켰다.
  2. 미래 end_date를 막는 검증이 전혀 없었다.
  3. PortfolioStock.symbol의 field_validator가 asset_type보다 먼저 선언되어 있어
     info.data.get('asset_type', 'stock')이 검증 시점에 asset_type을 전혀 보지
     못했다(아직 검증되지 않은 필드는 info.data에 없다 -- pydantic v2는 필드를
     선언 순서대로 검증한다). 그 결과 "현금 자산은 심볼 제한 없음" 분기가 한 번도
     실행되지 않는 죽은 코드였고, asset_type='cash'인데 이름이 "예금"처럼 한글이면
     정상적인 요청도 422로 거부됐다.

**수정 방향**:
- PortfolioStock: symbol 검증을 model_validator(mode='after')로 옮겨 선언 순서와
  무관하게 self.asset_type을 안전하게 참조한다. 같은 김에, 절대 발동하지 않던
  amount/weight 동시 입력 field_validator(자기 자신이 검증되는 시점엔 info.data에
  자기 값이 아직 없어 조건이 항상 False였다 -- 이것도 동일한 종류의 순서 의존
  버그)를 제거했다. 동일 케이스(한 종목에 amount와 weight 모두 입력)는
  PortfolioBacktestRequest.validate_portfolio가 포트폴리오 레벨에서 이미 정확히
  잡아내고 있었으므로(제거 전에도 최종 결과는 422로 동일), 죽은 코드를 지우는 것만
  으로 "규칙은 정확히 한 곳에서만 실행" 원칙에 맞춘다 (TestAmountWeightExclusivity
  참고).
- PortfolioBacktestRequest: rebalance_frequency에 FREQUENCY_MAP ∪ {'none'} 멤버십
  field_validator를 추가하고, end_date의 기존 field_validator에 "미래 날짜 금지"를
  추가했다. 부수적으로 기존 `end < start`를 `end <= start`로 좁혀 0일짜리 기간도
  막았다 (에러 메시지 "종료 날짜는 시작 날짜보다 이후여야 합니다"의 의미상 원래도
  그래야 했다).
- app/validators/portfolio_validator.py는 삭제했고 app/validators/__init__.py에서
  해당 export를 제거했다. DateValidator/SymbolValidator/BacktestValidator는
  app/services/validation_service.py가 여전히 사용하므로 그대로 유지했다.
- 최소 백테스트 기간(30일) 검증은 스키마가 아니라 app/api/v1/endpoints/backtest.py의
  엔드포인트 레벨에 추가했다. 이유: PortfolioBacktestRequest를 직접 생성해 DCA/
  리밸런싱/시뮬레이션 엔진만 단위테스트하는 기존 테스트들(예:
  tests/unit/test_dca_schedule_alignment.py L126-127, L192,
  tests/unit/test_portfolio_manager_batch4_fixes.py L293-294/345-346/397-398,
  tests/unit/test_portfolio_calculator_equity_curve.py L38-39,
  tests/unit/test_simulation_engine_async_offload.py L110-111)이 3~14일짜리 짧은
  기간을 사용한다. 스키마에 30일 하한을 넣으면 이 테스트들이 전부 깨진다. 반면
  실제 HTTP 요청만 거치는 엔드포인트 레벨에 두면 그 테스트들에는 전혀 영향을 주지
  않으면서 실제 사용자 요청은 여전히 막을 수 있다.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import ValidationError as PydanticValidationError
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.schemas import PortfolioStock, PortfolioBacktestRequest, FREQUENCY_MAP

pytestmark = pytest.mark.unit

client = TestClient(app)


def _mock_stock_repository() -> MagicMock:
    """상장일 검증 단계(엔드포인트 초반)가 실제 DB를 건드리지 않도록 격리."""
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


@pytest.fixture(autouse=True)
def mock_stock_repository():
    with patch(
        "app.api.v1.endpoints.backtest.get_stock_repository",
        return_value=_mock_stock_repository(),
    ):
        yield


class TestCashItemWithCustomKoreanName:
    """(a) asset_type='cash'인 항목은 커스텀 한글 이름을 허용해야 한다."""

    def test_cash_item_named_deposit_is_accepted(self):
        """RED(수정 전): PortfolioStock(symbol="예금", asset_type="cash")는
        ValidationError("주식 심볼은 영문자, 숫자, 점(.), 하이픈(-)만 포함해야
        합니다.")를 던졌다 (필드 선언 순서 버그로 asset_type='cash' 분기가
        실행되지 않음)."""
        stock = PortfolioStock(symbol="예금", asset_type="cash", amount=1000.0)
        assert stock.symbol == "예금"
        assert stock.asset_type == "cash"

    def test_cash_item_named_deposit_accepted_inside_full_request(self):
        """PortfolioBacktestRequest 전체 조립 경로에서도 동일하게 통과해야 한다."""
        request = PortfolioBacktestRequest(
            portfolio=[
                {"symbol": "AAPL", "amount": 5000.0, "asset_type": "stock"},
                {"symbol": "예금", "amount": 3000.0, "asset_type": "cash"},
            ],
            start_date="2023-01-01",
            end_date="2023-12-31",
            strategy="buy_hold_strategy",
        )
        cash_items = [p for p in request.portfolio if p.asset_type == "cash"]
        assert len(cash_items) == 1
        assert cash_items[0].symbol == "예금"

    def test_stock_symbol_format_is_still_enforced(self):
        """회귀 방지: asset_type='stock'(기본값)인 항목은 여전히 형식 검증을 받는다."""
        with pytest.raises(PydanticValidationError):
            PortfolioStock(symbol="invalid symbol!", amount=1000.0)

    def test_literal_cash_symbol_still_uppercased_without_explicit_asset_type(self):
        """회귀 방지: symbol='cash'(소문자)만 보내고 asset_type을 생략해도 기존처럼
        'CASH'로 대문자화되어 특별 심볼로 허용된다."""
        stock = PortfolioStock(symbol="cash", amount=1000.0)
        assert stock.symbol == "CASH"


class TestAmountWeightExclusivity:
    """부수 발견: PortfolioStock의 amount/weight 동시입력 field_validator는
    선언 순서 버그로 절대 발동하지 않는 죽은 코드였다 (자기 필드 자신의 값은
    검증 시점에 info.data에 없다). 동일 케이스는 PortfolioBacktestRequest.
    validate_portfolio가 포트폴리오 레벨에서 이미 정확히 잡아내므로, 이 죽은
    코드를 제거해도 최종 사용자에게 보이는 동작(422 거부)은 바뀌지 않는다."""

    def test_single_item_with_both_amount_and_weight_still_rejected_via_request(self):
        with pytest.raises(PydanticValidationError) as exc_info:
            PortfolioBacktestRequest(
                portfolio=[{"symbol": "AAPL", "amount": 100.0, "weight": 50.0}],
                start_date="2023-01-01",
                end_date="2023-12-31",
                strategy="buy_hold_strategy",
            )
        assert "amount" in str(exc_info.value) or "weight" in str(exc_info.value)


class TestRebalanceFrequencyMembership:
    """(b) rebalance_frequency는 FREQUENCY_MAP ∪ {'none'} 멤버십을 강제해야 한다."""

    def test_nonsense_rebalance_frequency_is_rejected(self):
        """RED(수정 전): rebalance_frequency: str 필드에 커스텀 field_validator가
        전혀 없어 'nonsense' 같은 값도 그대로 통과했다."""
        with pytest.raises(PydanticValidationError) as exc_info:
            PortfolioBacktestRequest(
                portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
                start_date="2023-01-01",
                end_date="2023-12-31",
                strategy="buy_hold_strategy",
                rebalance_frequency="nonsense",
            )
        assert "리밸런싱" in str(exc_info.value)

    def test_none_rebalance_frequency_still_accepted(self):
        """회귀 방지: 리밸런싱을 끄는 특수값 'none'은 계속 허용된다."""
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
            start_date="2023-01-01",
            end_date="2023-12-31",
            strategy="buy_hold_strategy",
            rebalance_frequency="none",
        )
        assert request.rebalance_frequency == "none"

    def test_all_frequency_map_keys_still_accepted(self):
        """회귀 방지: FREQUENCY_MAP에 정의된 모든 실제 값은 계속 허용된다."""
        for freq in FREQUENCY_MAP:
            request = PortfolioBacktestRequest(
                portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
                start_date="2023-01-01",
                end_date="2025-01-01",
                strategy="buy_hold_strategy",
                rebalance_frequency=freq,
            )
            assert request.rebalance_frequency == freq


class TestFutureEndDateRejected:
    """(c) 미래 end_date는 거부되어야 한다."""

    def test_future_end_date_is_rejected(self):
        """RED(수정 전): end_date의 field_validator는 start_date와의 순서/최대기간만
        검사했고 "오늘" 대비 검증이 전혀 없어 미래 날짜가 그대로 통과했다."""
        future = (date.today() + timedelta(days=365)).isoformat()
        past = (date.today() - timedelta(days=200)).isoformat()
        with pytest.raises(PydanticValidationError) as exc_info:
            PortfolioBacktestRequest(
                portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
                start_date=past,
                end_date=future,
                strategy="buy_hold_strategy",
            )
        assert "미래" in str(exc_info.value)

    def test_past_end_date_still_accepted(self):
        """회귀 방지: 과거 날짜는 계속 허용된다."""
        request = PortfolioBacktestRequest(
            portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
            start_date="2023-01-01",
            end_date="2023-12-31",
            strategy="buy_hold_strategy",
        )
        assert request.end_date == "2023-12-31"

    def test_end_date_equal_to_start_date_is_rejected(self):
        """부수적으로 발견한 off-by-one: 기존 코드는 end < start만 거부해 0일짜리
        기간(end == start)을 허용했다. 에러 메시지("종료 날짜는 시작 날짜보다
        이후여야 합니다")의 의미상 이미 거부됐어야 한다."""
        with pytest.raises(PydanticValidationError):
            PortfolioBacktestRequest(
                portfolio=[{"symbol": "AAPL", "amount": 1000.0}],
                start_date="2023-01-01",
                end_date="2023-01-01",
                strategy="buy_hold_strategy",
            )


class TestMinimumBacktestPeriodAtEndpoint:
    """엔드포인트 레벨 최소 기간(30일) 검증. 스키마가 아니라
    app/api/v1/endpoints/backtest.py에 두는 이유는 이 파일 상단 docstring 참고."""

    BASE_PAYLOAD = {
        "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
        "strategy": "buy_hold_strategy",
    }

    def test_period_shorter_than_30_days_returns_422(self):
        """RED(수정 전): 엔드포인트에 기간 하한 검사가 전혀 없어 9일짜리 요청이
        서비스 계층까지 그대로 도달했다 (아래에서 서비스 계층을 모킹해 성공
        응답을 주더라도, 수정 전에는 그 모킹된 성공 응답이 200으로 그대로
        반환됐다 -- 실제로 이 테스트를 수정 전 코드에 대해 실행하면 422가 아닌
        200이 나와서 실패한다)."""
        success_result = {
            "status": "success",
            "data": {"portfolio_statistics": {}, "individual_returns": {}},
        }
        unified_data = {
            "sp500_benchmark": [],
            "nasdaq_benchmark": [],
            "exchange_rates": {},
            "latest_news": [],
        }
        payload = {
            **self.BASE_PAYLOAD,
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",  # 9일
        }
        with patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(return_value=success_result),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value=unified_data,
        ):
            response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 422, response.text
        assert "기간" in response.text

    def test_period_of_exactly_30_days_reaches_service_layer(self):
        """30일 이상이면 최소 기간 검증은 통과하고(서비스 계층까지 도달), 성공
        응답을 받는다 (서비스/데이터 계층은 모킹)."""
        success_result = {
            "status": "success",
            "data": {"portfolio_statistics": {}, "individual_returns": {}},
        }
        unified_data = {
            "sp500_benchmark": [],
            "nasdaq_benchmark": [],
            "exchange_rates": {},
            "latest_news": [],
        }
        payload = {
            **self.BASE_PAYLOAD,
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",  # 정확히 30일
        }
        with patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(return_value=success_result),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value=unified_data,
        ):
            response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 200, response.text
