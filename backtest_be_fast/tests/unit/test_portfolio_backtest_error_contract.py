"""
포트폴리오 백테스트 API 에러 계약(Error Contract) 회귀 테스트 (P1-09 + P2-29)

**버그 배경**:
PortfolioManagerService.run_portfolio_backtest() / run_strategy_portfolio_backtest() /
run_buy_and_hold_portfolio_backtest()는 각각 자신의 전체 본문을 `except Exception`으로
감싸고, 어떤 예외가 발생하든 {'status': 'error', 'error': str(e), 'code': ...} 딕셔너리를
"정상적으로 return"했다. 엔드포인트(app/api/v1/endpoints/backtest.py)는 이 딕셔너리를
`if backtest_result.get('status') != 'success': return backtest_result`로 그대로
클라이언트에 전달했다.

결과적으로:
  1. 모든 백엔드 오류(검증 실패, 데이터 없음, 원시 버그)가 HTTP 200으로 응답되어
     @handle_portfolio_errors 데코레이터(422/404/429/500 매핑)가 완전히 무력화됨.
  2. 원본 예외 메시지(DB 연결 문자열, 파일 경로 등 내부 정보 포함 가능)가 그대로
     클라이언트에 노출됨.

이 테스트는 FastAPI TestClient로 엔드포인트 전체(라우팅 + @handle_portfolio_errors
데코레이터 포함)를 검증하되, PortfolioManagerService와 StockRepository를 모킹하여
DB/네트워크 호출 없이 tests/unit에서 격리 실행 가능하도록 만든다.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import DataNotFoundError, ValidationError

pytestmark = pytest.mark.unit

client = TestClient(app)

VALID_PAYLOAD = {
    "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
    "start_date": "2023-01-01",
    "end_date": "2023-06-30",
    "strategy": "buy_hold_strategy",
}


def _mock_stock_repository() -> MagicMock:
    """상장일 검증 단계(엔드포인트 초반)가 실제 DB를 건드리지 않도록 격리."""
    repo = MagicMock()
    repo.get_tickers_info_batch.return_value = {}
    return repo


@pytest.fixture(autouse=True)
def mock_stock_repository():
    """모든 테스트에서 엔드포인트의 상장일 검증이 DB 없이 통과하도록 패치."""
    with patch(
        "app.api.v1.endpoints.backtest.get_stock_repository",
        return_value=_mock_stock_repository(),
    ):
        yield


def _patch_deep_data_load(side_effect: Exception):
    """
    PortfolioManagerService.run_portfolio_backtest()의 최상위 try/except를
    직접 모킹하면 그 메서드 자신이 가진 버그(catch-all)를 우회해버려 아무것도
    검증하지 못한다. 대신 run_buy_and_hold_portfolio_backtest() 내부에서
    실제로 호출되는 self.data_loader.load_stock_data_parallel()을 모킹해,
    진짜 서비스 코드(및 그 안의 except 블록)가 그대로 실행되도록 한다.

    VALID_PAYLOAD는 strategy='buy_hold_strategy'이므로
    run_portfolio_backtest -> run_buy_and_hold_portfolio_backtest ->
    self.data_loader.load_stock_data_parallel() 순서로 실제 코드가 실행되다가
    이 지점에서 예외가 발생한다 (버그 사이트 #3, 오늘은 여기서 캐치되어
    {'status': 'error', ...} 딕셔너리로 뭉개짐).
    """
    return patch(
        "app.services.portfolio.portfolio_data_loader.PortfolioDataLoader.load_stock_data_parallel",
        new=AsyncMock(side_effect=side_effect),
    )


class TestPortfolioBacktestErrorContract:
    """POST /api/v1/backtest 의 에러 응답 계약 검증

    아래 세 테스트는 PortfolioManagerService의 진짜 코드 경로
    (run_portfolio_backtest -> run_buy_and_hold_portfolio_backtest)를 그대로
    실행시키고, 그 안에서 실제로 호출되는 데이터 로더만 모킹한다.
    엔드포인트 레벨(portfolio_manager_service.run_portfolio_backtest 자체)을
    모킹하면 버그가 있는 catch-all을 건너뛰어버려 아무 것도 검증하지 못하므로
    반드시 이 방식을 유지해야 한다.
    """

    def test_generic_exception_returns_500_not_200_and_does_not_leak_internals(self):
        """
        RED (수정 전): 서비스 내부에서 임의의 예외가 발생하면 버그 있는 코드는
        200 + {'status': 'error', 'error': '<원본 메시지 그대로>'}를 반환한다.
        이는 (a) 실패를 성공(200)으로 위장하고 (b) 내부 정보를 그대로 노출한다.

        GREEN (수정 후): 예외가 @handle_portfolio_errors까지 전파되어 500과
        불투명한 오류 ID 메시지만 반환해야 하며, 원본 예외 텍스트는 응답 본문
        어디에도 나타나서는 안 된다.
        """
        leaked_secret = "DB connection string leaked here: postgresql://user:pw@10.0.0.5/prod"
        with _patch_deep_data_load(Exception(leaked_secret)):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 500, (
            f"내부 예외가 발생했는데 상태 코드가 500이 아님: "
            f"{response.status_code}, body={response.text}"
        )
        assert leaked_secret not in response.text, (
            "내부 예외 메시지가 응답 본문에 그대로 노출됨 (정보 유출, P2-29)"
        )
        body = response.json()
        assert "오류 ID" in body.get("detail", ""), (
            f"불투명한 오류 ID 메시지가 아님: {body}"
        )

    def test_validation_error_returns_422(self):
        """RED (수정 전): ValidationError조차 200으로 응답됨.
        GREEN (수정 후): ValidationError는 422로 변환되어야 한다."""
        with _patch_deep_data_load(
            ValidationError("포트폴리오 구성이 올바르지 않습니다.")
        ):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 422, (
            f"ValidationError가 422로 변환되지 않음: {response.status_code}, "
            f"body={response.text}"
        )
        assert "포트폴리오 구성이 올바르지 않습니다" in response.text

    def test_data_not_found_error_returns_its_documented_status_code(self):
        """DataNotFoundError는 app/core/exceptions.py에 정의된 대로
        404 Not Found를 반환해야 한다 (오늘은 200으로 뭉개짐)."""
        with _patch_deep_data_load(
            DataNotFoundError("AAPL", "2023-01-01", "2023-06-30")
        ):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 404, (
            f"DataNotFoundError가 404로 전파되지 않음: {response.status_code}, "
            f"body={response.text}"
        )
        assert "AAPL" in response.text

    def test_success_path_still_returns_200_with_unchanged_shape(self):
        """회귀 방지: 성공 응답의 형태(status='success' + data)는 이번 수정으로
        바뀌지 않아야 한다. 오직 에러 경로만 바뀐다."""
        success_result = {
            "status": "success",
            "data": {
                "portfolio_statistics": {"Total_Return": 12.3},
                "individual_returns": {},
            },
        }
        unified_data = {
            "sp500_benchmark": [],
            "nasdaq_benchmark": [],
            "exchange_rates": {},
            "latest_news": [],
        }
        with patch(
            "app.api.v1.endpoints.backtest.portfolio_manager_service.run_portfolio_backtest",
            new=AsyncMock(return_value=success_result),
        ), patch(
            "app.api.v1.endpoints.backtest.unified_data_service.collect_all_unified_data",
            return_value=unified_data,
        ):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "success"
        assert body["data"]["portfolio_statistics"]["Total_Return"] == 12.3
        assert body["data"]["sp500_benchmark"] == []
