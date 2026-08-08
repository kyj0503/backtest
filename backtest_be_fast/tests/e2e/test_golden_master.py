
import math
import pytest
import pandas as pd
import json
import os
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

# Load mock data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# --- Golden Master 재생성 방법 (P1-13) ---------------------------------------
# 이 파일은 예전에 "기대 파일이 없으면 현재 출력으로 자동 생성 후 통과"했다.
# 그 동작 자체가 버그였다 (첫 실행이 항상 기준이 되어버려 절대 실패할 수 없는
# 테스트가 됨). 자동 생성은 완전히 제거했고, 재생성은 아래처럼 명시적으로만 한다:
#
#   REGENERATE_GOLDEN_MASTER=1 docker compose -f compose.dev.yaml exec -T \
#       backtest-be-fast pytest tests/e2e/test_golden_master.py -m e2e -q
#
# 위 명령은 tests/e2e/data/expected_dca_output.json을 현재 코드의 실제 출력으로
# 덮어쓰고 테스트를 skip 처리한다(재생성 자체를 pass로 위장하지 않기 위함).
# 재생성 후에는 반드시:
#   1) git diff로 새/구 수치를 사람이 검토해 "회귀"가 아니라 "의도된 변경"인지 확인하고
#   2) REGENERATE_GOLDEN_MASTER 없이 다시 실행해 정말로 통과하는지 확인한 뒤 커밋한다.
REGENERATE_ENV_VAR = "REGENERATE_GOLDEN_MASTER"

# 부동소수점 허용오차: JSON round-trip, pandas/numpy 버전 차이 등으로 인한
# bit-for-bit 불일치만 흡수한다. 실제 로직 회귀(DCA 회차 수, 커미션 반영 여부,
# 리밸런싱 결과 등)는 반드시 잡아내야 하므로 느슨하게 잡지 않는다.
_REL_TOL = 1e-6
_ABS_TOL = 1e-6


def _assert_golden_match(actual, expected, path="data"):
    """골든 파일과 실제 결과를 재귀적으로 비교한다.

    dict/list는 구조(키 집합, 길이)까지 비교하고, float는 상대/절대 허용오차
    내에서 비교한다. 그 외 타입(문자열, 정수, bool 등)은 완전 일치를 요구한다.
    """
    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: dict가 아님 (actual={type(actual).__name__})"
        missing = set(expected.keys()) - set(actual.keys())
        extra = set(actual.keys()) - set(expected.keys())
        assert not missing, f"{path}: 실제 결과에 없는 키 (골든에는 있음): {sorted(missing)}"
        assert not extra, f"{path}: 실제 결과에만 있는 새 키 (골든에는 없음): {sorted(extra)}"
        for key in expected:
            _assert_golden_match(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: list가 아님 (actual={type(actual).__name__})"
        assert len(actual) == len(expected), (
            f"{path}: 길이 불일치 actual={len(actual)} expected={len(expected)}"
        )
        for i, (a_item, e_item) in enumerate(zip(actual, expected)):
            _assert_golden_match(a_item, e_item, f"{path}[{i}]")
    elif isinstance(expected, float):
        assert isinstance(actual, (int, float)), f"{path}: 숫자가 아님 (actual={actual!r})"
        assert math.isclose(actual, expected, rel_tol=_REL_TOL, abs_tol=_ABS_TOL), (
            f"{path}: 값 불일치 actual={actual!r} expected={expected!r}"
        )
    else:
        assert actual == expected, f"{path}: 값 불일치 actual={actual!r} expected={expected!r}"

def load_mock_csv(ticker):
    path = os.path.join(DATA_DIR, f"{ticker}.csv")
    if os.path.exists(path):
        print(f"Loading mock CSV from {path}")
        df = pd.read_csv(path)
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        return df
    print(f"Mock CSV not found at {path}")
    return pd.DataFrame()

class MockStockRepository:
    def load_stock_data(self, ticker, start_date=None, end_date=None, **kwargs):
        print(f"MockStockRepository.load_stock_data called for {ticker} ({start_date}-{end_date})")
        df = load_mock_csv(ticker)
        if df.empty:
            print("Empty DF loaded")
            return df
        
        # Filter by date if needed
        if start_date:
            df = df[df.index >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df.index <= pd.to_datetime(end_date)]
            
        print(f"Returned {len(df)} rows")
        return df

    def get_tickers_info_batch(self, tickers):
        return {
            t: {'currency': 'USD', 'symbol': t} for t in tickers
        }
        
    def get_ticker_info(self, ticker):
        return {'currency': 'USD', 'symbol': ticker}

    def load_ticker_news(self, ticker, max_age_hours=3):
        return []

    def save_stock_data(self, ticker, df):
        return 0

@pytest.fixture
def mock_stock_repo():
    return MockStockRepository()

@pytest.fixture
def mock_currency_converter():
    mock = AsyncMock()
    mock.load_multiple_exchange_rates.return_value = {
        'KRW': {
            '2023-01-01': 1300.0
        }
    }
    mock.get_exchange_rate.return_value = 1.0
    return mock

@pytest.mark.e2e
def test_golden_master_backtest_dca(mock_stock_repo, mock_currency_converter):
    """
    Golden Master Test for DCA Portfolio
    """
    # Mock unified data service
    mock_unified_service = MagicMock()
    mock_unified_service.collect_all_unified_data.return_value = {
        'status': 'success',
        'sp500_benchmark': [],
        'nasdaq_benchmark': [], 
        'latest_news': [],
        'exchange_rates': {}
    }

    # Patch the INSTANCE in endpoints because it's global
    # And specifically patch the StockRepository instance used by the service
    #
    # NOTE (found while fixing P1-13): PortfolioManagerService.__init__ builds
    # self.data_loader = PortfolioDataLoader(stock_repository=self.stock_repository,
    # currency_converter=currency_converter) ONCE at singleton-construction time
    # (module import). PortfolioDataLoader.__init__ copies those into its own
    # self.stock_repository / self.currency_converter attributes. Patching only
    # portfolio_manager_service.stock_repository (below) therefore does NOT
    # reach the nested data_loader — it kept its own captured reference to the
    # REAL repository/currency converter. Every actual price load in the DCA
    # flow goes through self.data_loader.load_stock_data_parallel() /
    # load_ticker_currencies(), so without the two extra patches below this
    # test silently fetched real (possibly DB-cached) AAPL price data instead
    # of tests/e2e/data/AAPL.csv -- undetectable while the only assertion was
    # `status == 'success'`, but it broke the numeric comparison added for
    # P1-13 (real cached AAPL close prices don't match the synthetic fixture).
    # tests/unit/test_portfolio_backtest_error_contract.py hit the same
    # pitfall and worked around it by patching PortfolioDataLoader.load_stock_data_parallel
    # directly; patching the nested attributes here keeps this test closer to
    # a real end-to-end run while still being fully hermetic.
    with patch("app.api.v1.endpoints.backtest.portfolio_manager_service.stock_repository", mock_stock_repo), \
         patch("app.api.v1.endpoints.backtest.portfolio_manager_service.data_loader.stock_repository", mock_stock_repo), \
         patch("app.api.v1.endpoints.backtest.portfolio_manager_service.data_loader.currency_converter", mock_currency_converter), \
         patch("app.services.portfolio_manager_service.currency_converter", mock_currency_converter), \
         patch("app.api.v1.endpoints.backtest.get_stock_repository", return_value=mock_stock_repo), \
         patch("app.api.v1.endpoints.backtest.unified_data_service", mock_unified_service):
        
        client = TestClient(app)
        
        payload = {
            "portfolio": [
                {
                    "symbol": "AAPL",
                    "amount": 1000.0,
                    "investment_type": "dca",
                    "dca_frequency": "weekly_1"
                }
            ],
            "start_date": "2023-01-01",
            "end_date": "2023-01-12",
            "strategy": "buy_hold_strategy"
        }
        
        response = client.post("/api/v1/backtest", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

        result = response.json()

        # Define expected output file path
        expected_file = os.path.join(DATA_DIR, "expected_dca_output.json")

        # 명시적 재생성 모드 (자동 생성은 절대 하지 않는다 — 위 모듈 docstring 참고)
        if os.environ.get(REGENERATE_ENV_VAR) == "1":
            with open(expected_file, "w") as f:
                json.dump(result, f, indent=2, sort_keys=True)
            pytest.skip(
                f"{REGENERATE_ENV_VAR}=1 로 골든 마스터를 재생성했습니다: {expected_file}\n"
                "재생성된 수치를 diff로 검토한 뒤, 이 환경변수 없이 다시 실행해 "
                "통과하는지 확인하세요."
            )

        if not os.path.exists(expected_file):
            pytest.fail(
                f"골든 마스터 파일이 없습니다: {expected_file}\n"
                "자동 생성은 의도적으로 비활성화되어 있습니다 (부재 시 항상 통과하던 "
                "버그를 재도입하지 않기 위함, P1-13). 재생성하려면:\n"
                f"  {REGENERATE_ENV_VAR}=1 pytest tests/e2e/test_golden_master.py -m e2e -q"
            )

        with open(expected_file, "r") as f:
            expected = json.load(f)

        assert result['status'] == expected['status']
        # data 부분을 수치 허용오차 내에서 재귀 비교 (기존에는 상태 문자열만 비교했음)
        _assert_golden_match(result['data'], expected['data'])
