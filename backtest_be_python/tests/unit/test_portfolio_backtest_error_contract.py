"""
포트폴리오 백테스트 API 에러 계약(Error Contract) 회귀 테스트 (P1-09 + P2-29)

서비스 내부 예외는 HTTP 200 {'status': 'error'}로 뭉개지지 않고 @handle_portfolio_errors까지
전파되어 상태 코드로 매핑되어야 한다. 원본 예외 메시지(내부 정보)는 응답에 노출되지 않는다.

시세 조회(app.engine.source.Source.history)만 모킹하고 계산·부가 데이터 경로는 실제 코드를 돌린다.
"""
from datetime import date
from unittest.mock import patch

import pytest

from fastapi.testclient import TestClient

from app.main import app
from app.core.exceptions import DataNotFoundError, ValidationError, YfinanceRateLimitError
from app.engine.errors import not_found, unavailable
from app.engine.marketdata import Bar, History
from app.engine.source import source

pytestmark = pytest.mark.unit

client = TestClient(app)

VALID_PAYLOAD = {
    "portfolio": [{"symbol": "AAPL", "amount": 10000.0}],
    "start_date": "2023-01-02",
    "end_date": "2023-06-30",
    "strategy": "buy_hold_strategy",
}


@pytest.fixture(autouse=True)
def _clear_price_cache():
    source.clear()
    yield
    source.clear()


def _patch_deep_data_load(side_effect: Exception):
    """시세 조회 지점에서 예외를 낸다. 그 위의 실제 서비스 코드는 그대로 실행된다."""
    return patch("app.engine.source.Source.history", side_effect=side_effect)


class TestPortfolioBacktestErrorContract:
    """POST /api/v1/backtest 의 에러 응답 계약 검증"""

    def test_generic_exception_returns_500_not_200_and_does_not_leak_internals(self):
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

    def test_rate_limit_error_returns_429_with_retry_after(self):
        """YfinanceRateLimitError는 app/core/exceptions.py에 정의된 자신의
        상태 코드(429)로 그대로 전파되어야 하며, Retry-After 헤더도 함께
        내려가야 한다. handle_portfolio_errors의 docstring이 문서화하는
        '422/404/429/500 매핑' 중 429는 이 파일에서 지금까지 검증되지
        않았던 마지막 매핑이다 (P2-37)."""
        with _patch_deep_data_load(YfinanceRateLimitError(30)):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 429, (
            f"YfinanceRateLimitError가 429로 전파되지 않음: {response.status_code}, "
            f"body={response.text}"
        )
        assert response.headers.get("Retry-After") == "30", (
            f"Retry-After 헤더가 누락되거나 값이 다름: {response.headers.get('Retry-After')!r}"
        )

    def test_provider_unavailable_returns_503_with_retry_after(self):
        with _patch_deep_data_load(unavailable("AAPL: 시세의 OHLC 범위가 일치하지 않습니다.")):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)
        assert response.status_code == 503, response.text
        assert response.headers.get("Retry-After") == "30"
        assert response.json() == {"detail": "AAPL: 시세의 OHLC 범위가 일치하지 않습니다."}

    def test_every_symbol_missing_returns_422(self):
        """없는 종목(404)은 경고와 함께 빠지고, 남는 항목이 없으면 422다(Go와 같은 문구)."""
        with _patch_deep_data_load(not_found("가격 데이터가 없습니다: AAPL")):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)
        assert response.status_code == 422, response.text
        assert response.json() == {"detail": "[ValidationError] 포트폴리오의 어떤 종목도 데이터를 가져올 수 없습니다."}

    def test_success_path_returns_200_with_documented_shape(self):
        start, end = date(2023, 1, 2).toordinal(), date(2023, 6, 30).toordinal()

        def history(symbol, s, e):
            if symbol != "AAPL":
                raise not_found(f"가격 데이터가 없습니다: {symbol}")
            return History(symbol="AAPL", currency="USD", company_name="Apple", exchange="NMS",
                           bars=[Bar(d, 100.0, 100.0, 100.0, 100.0) for d in range(start, end + 1)])

        with _patch_deep_data_load(history):
            response = client.post("/api/v1/backtest", json=VALID_PAYLOAD)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "success"
        data = body["data"]
        assert list(data)[:12] == [
            "portfolio_statistics", "individual_returns", "individual_results", "portfolio_result",
            "portfolio_composition", "equity_curve", "daily_returns", "strategy_details",
            "rebalance_history", "weight_history", "warnings", "calculation_assumptions",
        ]
        # 벤치마크(^GSPC)는 없으므로 섹션 오류로 비우고 핵심 결과는 그대로 준다.
        assert data["sp500_benchmark"] == []
        assert data["supplemental_status"]["benchmarks"] == "error"
        assert data["ticker_info"]["AAPL"]["company_name"] == "Apple"
        # 수수료 0.2%: 매수 예산 B로 B/(1+c)어치를 산다(F02).
        assert data["portfolio_statistics"]["Final_Value"] == pytest.approx(10000 / 1.002)
