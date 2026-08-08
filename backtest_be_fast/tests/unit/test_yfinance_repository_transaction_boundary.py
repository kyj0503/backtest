"""yfinance_repository DB 트랜잭션 경계 회귀 테스트 (P2-10)

YFinanceRepository는 두 지점에서 외부 네트워크 호출(yfinance)을 DB
트랜잭션/커넥션이 열려 있는 동안 수행했다:

  1. save_ticker_data() -> _save_stock_metadata()가 engine.begin() 트랜잭션
     "안에서" data_fetcher.fetch_ticker_info(ticker)를 호출했다.
  2. get_ticker_info_from_db()가 engine.connect() 커넥션을 쥔 채로
     data_fetcher.fetch_ticker_info(ticker)를 호출하고, 그 결과로 또 다른
     트랜잭션을 여는 _update_ticker_info()까지 호출했다.

Yahoo 응답이 느려지면 그만큼 커넥션 풀의 커넥션(및 1의 경우 트랜잭션 락)을
오래 붙잡아 다른 요청을 굶긴다 - _retry_on_deadlock이 존재하는 이유이기도 하다.

수정: 두 지점 모두 네트워크 조회를 트랜잭션/커넥션을 열기 "전에" 미리 수행하고,
DB 쓰기만을 위한 짧은 트랜잭션을 그 다음에 연다.

이 테스트는 실제 SQLAlchemy Engine 대신, begin()/connect() 컨텍스트 매니저에
진입/종료할 때 (중첩을 고려해) depth 카운터를 증감시키는 가짜 엔진을 주입해
"네트워크 호출 시점에 트랜잭션/커넥션이 열려 있는가(depth > 0)"를 직접
관찰한다. SQL 문자열은 일부 패턴(needle)으로만 매칭해 결과를 반환하며, 쿼리
문법 자체의 정확성은 검증하지 않는다 (그건 integration 테스트의 몫).
"""
import json
from contextlib import contextmanager

import pandas as pd
import pytest

from app.repositories.yfinance_repository import YFinanceRepository


pytestmark = pytest.mark.unit


class _FakeResult:
    """conn.execute(...)의 반환값을 흉내낸다 (fetchone만 지원하면 충분하다)."""

    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _FakeConnection:
    """SQL 문자열의 일부(needle)로 미리 정해둔 결과를 반환하는 가짜 커넥션."""

    def __init__(self, responses):
        self._responses = responses  # List[Tuple[str, list]]
        self.executed_sql = []

    def execute(self, stmt, params=None):
        sql = str(stmt)
        self.executed_sql.append(sql)
        for needle, rows in self._responses:
            if needle in sql:
                return _FakeResult(rows)
        return _FakeResult([])  # 매칭 안 되는 문(INSERT 등)은 빈 결과로 충분


class _TransactionFlagEngine:
    """begin()/connect() 진입 중에는 depth를 올리고, 종료되면 내리는 가짜 엔진.

    중첩 호출(예: connect() 안에서 begin()이 또 열리는 경우)도 정확히
    반영하도록 depth 카운터를 사용한다 - 단순 bool 플래그는 안쪽 컨텍스트가
    먼저 빠져나올 때 바깥쪽이 아직 열려 있는데도 False로 잘못 떨어질 수 있다.
    """

    def __init__(self, state, responses):
        self.state = state  # {'depth': int}
        self.connection = _FakeConnection(responses)

    @contextmanager
    def begin(self):
        self.state['depth'] = self.state.get('depth', 0) + 1
        try:
            yield self.connection
        finally:
            self.state['depth'] -= 1

    @contextmanager
    def connect(self):
        self.state['depth'] = self.state.get('depth', 0) + 1
        try:
            yield self.connection
        finally:
            self.state['depth'] -= 1


@pytest.fixture
def repository():
    return YFinanceRepository()


def _minimal_price_df():
    return pd.DataFrame(
        {"Open": [1.0], "High": [1.0], "Low": [1.0], "Close": [1.0], "Volume": [100]},
        index=pd.to_datetime(["2023-01-01"]),
    )


class TestSaveTickerDataFetchesInfoOutsideTransaction:
    """save_ticker_data(): fetch_ticker_info는 engine.begin() 트랜잭션 밖에서
    호출되어야 한다. 오늘은 트랜잭션 안(_save_stock_metadata)에서 호출된다."""

    def test_fetch_ticker_info_is_not_called_while_transaction_open(
        self, repository, monkeypatch
    ):
        state = {'depth': 0}
        responses = [
            ("SELECT info_json FROM stocks", []),
            ("SELECT id FROM stocks", [(1,)]),
        ]
        fake_engine = _TransactionFlagEngine(state, responses)
        monkeypatch.setattr(repository, "_get_engine", lambda: fake_engine)

        observed_open_flags = []

        class _FakeDataFetcher:
            def fetch_ticker_info(self, ticker):
                observed_open_flags.append(state['depth'] > 0)
                return {"company_name": "Apple Inc.", "currency": "USD"}

        monkeypatch.setattr(repository, "data_fetcher", _FakeDataFetcher())

        saved_count = repository.save_ticker_data("AAPL", _minimal_price_df())

        assert observed_open_flags == [False], (
            "fetch_ticker_info가 DB 트랜잭션이 열려 있는 동안 호출됨: "
            f"{observed_open_flags}"
        )
        # 동작 보존: 여전히 저장된 행 수를 반환해야 한다
        assert saved_count == 1

    def test_fetch_ticker_info_failure_still_saves_with_defaults(
        self, repository, monkeypatch
    ):
        """기존 동작 보존: 외부 조회가 실패해도 저장 자체는 계속 진행되어야 한다."""
        state = {'depth': 0}
        responses = [
            ("SELECT info_json FROM stocks", []),
            ("SELECT id FROM stocks", [(1,)]),
        ]
        fake_engine = _TransactionFlagEngine(state, responses)
        monkeypatch.setattr(repository, "_get_engine", lambda: fake_engine)

        class _FailingDataFetcher:
            def fetch_ticker_info(self, ticker):
                raise ConnectionError("Yahoo 연결 실패")

        monkeypatch.setattr(repository, "data_fetcher", _FailingDataFetcher())

        saved_count = repository.save_ticker_data("AAPL", _minimal_price_df())

        assert saved_count == 1


class TestGetTickerInfoFromDbFetchesInfoOutsideConnection:
    """get_ticker_info_from_db(): DB에 상장일이 없어 Yahoo Finance를 조회하는
    경로에서, fetch_ticker_info는 engine.connect() 커넥션 밖에서 호출되어야
    한다. 오늘은 커넥션이 열린 채로 호출되고, 그 안에서 또 다른 트랜잭션
    (_update_ticker_info)까지 연다."""

    def test_fetch_ticker_info_is_not_called_while_connection_open(
        self, repository, monkeypatch
    ):
        state = {'depth': 0}
        existing_info_json = json.dumps(
            {
                "currency": "USD",
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
                # first_trade_date 없음 -> Yahoo Finance 조회 트리거 조건
            }
        )
        responses = [
            ("SELECT id, info_json FROM stocks", [(1, existing_info_json)]),
            ("UPDATE stocks SET info_json", []),
        ]
        fake_engine = _TransactionFlagEngine(state, responses)
        monkeypatch.setattr(repository, "_get_engine", lambda: fake_engine)

        observed_open_flags = []

        class _FakeDataFetcher:
            def fetch_ticker_info(self, ticker):
                observed_open_flags.append(state['depth'] > 0)
                return {"first_trade_date": "1980-12-12"}

        monkeypatch.setattr(repository, "data_fetcher", _FakeDataFetcher())

        result = repository.get_ticker_info_from_db("AAPL")

        assert observed_open_flags == [False], (
            "fetch_ticker_info가 DB 커넥션이 열려 있는 동안 호출됨: "
            f"{observed_open_flags}"
        )
        # 동작 보존: 새로 조회된 상장일이 병합되어 반환되어야 한다
        assert result["first_trade_date"] == "1980-12-12"
        assert result["company_name"] == "Apple Inc."
        assert result["currency"] == "USD"

    def test_no_yahoo_call_when_first_trade_date_already_present(
        self, repository, monkeypatch
    ):
        """회귀 방지: DB에 이미 상장일이 있으면 네트워크 호출 자체가 없어야 한다."""
        state = {'depth': 0}
        existing_info_json = json.dumps(
            {
                "currency": "USD",
                "company_name": "Apple Inc.",
                "exchange": "NASDAQ",
                "first_trade_date": "1980-12-12",
            }
        )
        responses = [("SELECT id, info_json FROM stocks", [(1, existing_info_json)])]
        fake_engine = _TransactionFlagEngine(state, responses)
        monkeypatch.setattr(repository, "_get_engine", lambda: fake_engine)

        call_count = {"n": 0}

        class _FakeDataFetcher:
            def fetch_ticker_info(self, ticker):
                call_count["n"] += 1
                return {}

        monkeypatch.setattr(repository, "data_fetcher", _FakeDataFetcher())

        result = repository.get_ticker_info_from_db("AAPL")

        assert call_count["n"] == 0
        assert result["first_trade_date"] == "1980-12-12"
