"""
DCA 및 리밸런싱 로직 통합 테스트

실제 DB/yfinance 데이터를 사용해 Nth Weekday 방식의 DCA와 리밸런싱이
제대로 작동하는지 검증합니다 (get_nth_weekday_of_month 등 순수 함수 자체의
단위 테스트는 tests/unit/test_nth_weekday.py, test_nth_weekday_edge_cases.py 참고).

**P2-40 변경 사항**:
- 마커 없음 -> `pytestmark = pytest.mark.integration` 추가. 기존에는 마커가
  없어 `pytest -m integration`으로는 이 파일이 전혀 수집되지 않았고, 반대로
  마커 없는 bare `pytest`는 이 파일을 수집해서 (서버가 떠 있지 않으면) 접속
  실패로 깨졌다.
- `requests` + `http://localhost:8000` 라이브 서버 의존 -> FastAPI
  `TestClient`로 전환. 별도로 `docker compose up`된 서버가 없어도 동작한다
  (다만 StockRepository/DB/yfinance는 모킹하지 않으므로 여전히 DB 연결과
  필요 시 외부 네트워크가 있어야 한다 -- 그래서 unit이 아니라 integration).
- 결과를 print만 하고 아무것도 assert하지 않던 부분을 실제 단언으로 교체.
  Total_Trades(거래 횟수)는 2024년치 실제 과거 시세 + 결정론적 DCA/리밸런싱
  스케줄링 로직의 함수이므로 재현 가능하다 (이미 지나간 과거 구간이라 시세가
  바뀔 일이 없다). Final_Value는 동일한 이유로 결정론적이지만 부동소수점
  경로 차이에 다소 민감할 수 있어 pytest.approx(rel=1e-4)로 비교한다.
  아래 기대값은 이 변경을 적용한 시점에 실제로 API를 호출해 관측한 값이다.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.integration

client = TestClient(app)


def test_monthly_dca():
    """매월 DCA 투자 테스트 (monthly_1): AAPL, 2024-01-10 ~ 2024-12-31, 12개월 -> 12회 매수"""
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            }
        ],
        "start_date": "2024-01-10",  # 2024년 1월 10일 (2번째 수요일)
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "none",
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, f"API Request failed: {response.text}"

    stats = response.json().get("data", {}).get("portfolio_statistics", {})

    assert stats.get("Total_Trades") == 12, (
        f"매월 DCA 12개월치는 12회 매수가 기대됨: {stats.get('Total_Trades')}"
    )
    assert stats.get("Final_Value") == pytest.approx(14760.989923900852, rel=1e-4)


def test_quarterly_rebalancing():
    """분기별 리밸런싱 테스트 (monthly_3): AAPL 50% + MSFT 50% lump sum, 2024년 4개 분기 리밸런싱"""
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "weight": 50
            },
            {
                "symbol": "MSFT",
                "weight": 50
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "monthly_3",  # 분기별
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, f"API Request failed: {response.text}"

    stats = response.json().get("data", {}).get("portfolio_statistics", {})

    # 최초 매수(2종목) + 분기별 리밸런싱(4회 x 2종목 리밸런스 거래) = 8회
    assert stats.get("Total_Trades") == 8, (
        f"최초 매수 2건 + 분기 리밸런싱 4회 x 2종목: {stats.get('Total_Trades')}"
    )
    assert stats.get("Final_Value") == pytest.approx(123.83673897419337, rel=1e-4)


def test_weekly_dca():
    """매주 DCA 투자 테스트 (weekly_1): SPY, 2024-01-10 ~ 2024-03-31 (약 12주) -> 12회 매수"""
    payload = {
        "portfolio": [
            {
                "symbol": "SPY",
                "amount": 100,
                "investment_type": "dca",
                "dca_frequency": "weekly_1"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-03-31",  # 3개월
        "commission": 0.001,
        "rebalance_frequency": "none",
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, f"API Request failed: {response.text}"

    stats = response.json().get("data", {}).get("portfolio_statistics", {})

    assert stats.get("Total_Trades") == 12, (
        f"2024-01-10~03-31 매주 DCA는 12회 매수가 기대됨: {stats.get('Total_Trades')}"
    )
    assert stats.get("Final_Value") == pytest.approx(1261.5411494713712, rel=1e-4)


def test_biweekly_dca():
    """2주마다 DCA 투자 테스트 (weekly_2): QQQ, 2024-01-10 ~ 2024-06-30 (약 6개월) -> 13회 매수"""
    payload = {
        "portfolio": [
            {
                "symbol": "QQQ",
                "amount": 200,
                "investment_type": "dca",
                "dca_frequency": "weekly_2"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-06-30",  # 6개월
        "commission": 0.001,
        "rebalance_frequency": "none",
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, f"API Request failed: {response.text}"

    stats = response.json().get("data", {}).get("portfolio_statistics", {})

    assert stats.get("Total_Trades") == 13, (
        f"2024-01-10~06-30 2주마다 DCA는 13회 매수가 기대됨: {stats.get('Total_Trades')}"
    )
    assert stats.get("Final_Value") == pytest.approx(2835.854201803439, rel=1e-4)


def test_combined_dca_and_rebalancing():
    """DCA + 리밸런싱 조합 테스트: AAPL/MSFT 각 월 DCA(12회 x 2종목) + 분기 리밸런싱(4회 x 2종목) = 30회"""
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            },
            {
                "symbol": "MSFT",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "monthly_1"
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "monthly_3",  # 분기별 리밸런싱
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)
    assert response.status_code == 200, f"API Request failed: {response.text}"

    stats = response.json().get("data", {}).get("portfolio_statistics", {})

    # 월 DCA 12회 x 2종목 + 분기 리밸런싱 4회 x 2종목 = 30회
    assert stats.get("Total_Trades") == 30, (
        f"월 DCA(12x2) + 분기 리밸런싱(4x2) = 30회가 기대됨: {stats.get('Total_Trades')}"
    )
    assert stats.get("Final_Value") == pytest.approx(26701.925381014917, rel=1e-4)


def test_legacy_frequency_should_fail():
    """잘못된 주기 요청은 거부되어야 함"""
    payload = {
        "portfolio": [
            {
                "symbol": "AAPL",
                "amount": 1000,
                "investment_type": "dca",
                "dca_frequency": "invalid_freq"  # 확실히 잘못된 주기
            }
        ],
        "start_date": "2024-01-10",
        "end_date": "2024-12-31",
        "commission": 0.002,
        "rebalance_frequency": "none",
        "strategy": "buy_hold_strategy"
    }

    response = client.post("/api/v1/backtest", json=payload)

    assert response.status_code == 422, f"Invalid frequency should be rejected but got {response.status_code}"
