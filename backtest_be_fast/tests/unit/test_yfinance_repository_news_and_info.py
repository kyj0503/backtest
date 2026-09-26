"""YFinanceRepository의 티커 메타데이터 조회·뉴스 저장/조회 특성화 테스트 (A-16)

yfinance_repository.py를 책임별로 나누기 전에, 기존 테스트가 다루지 않던
get_ticker_info_batch_from_db / load_news_from_db / save_news_to_db와
get_ticker_info_from_db의 기본값 경로의 현재 동작을 고정한다. 실제 DB 대신 SQL
문자열 일부로 결과를 돌려주고 실행된 문과 파라미터를 기록하는 가짜 엔진을 쓴다.
"""
import json
from contextlib import contextmanager
from datetime import date, datetime, timezone

import pytest

from app.repositories.yfinance_repository import YFinanceRepository

pytestmark = pytest.mark.unit


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class _Connection:
    def __init__(self, responses):
        self.responses = responses
        self.executed = []  # [(sql, params)]

    def execute(self, stmt, params=None):
        sql = " ".join(str(stmt).split())
        self.executed.append((sql, params))
        for needle, rows in self.responses:
            if needle in sql:
                return _Result(rows)
        return _Result([])


class _Engine:
    def __init__(self, responses=(), broken=False):
        self.connection = _Connection(list(responses))
        self.broken = broken
        self.opened = []

    @contextmanager
    def begin(self):
        if self.broken:
            raise RuntimeError("db down")
        self.opened.append("begin")
        yield self.connection

    @contextmanager
    def connect(self):
        if self.broken:
            raise RuntimeError("db down")
        self.opened.append("connect")
        yield self.connection


@pytest.fixture
def repository():
    return YFinanceRepository()


def _use(repository, monkeypatch, engine):
    monkeypatch.setattr(repository, "_get_engine", lambda: engine)
    return engine


class TestTickerInfoBatch:
    def test_rows_are_mapped_and_missing_tickers_get_defaults(self, repository, monkeypatch):
        engine = _use(repository, monkeypatch, _Engine([
            ("FROM stocks WHERE ticker IN", [
                ("AAPL", json.dumps({"currency": "USD", "company_name": "Apple",
                                     "exchange": "NASDAQ", "first_trade_date": "1980-12-12"})),
                ("005930.KS", json.dumps({"currency": "KRW"})),
                ("BROKEN", "{not json"),
                ("NULLINFO", None),
            ]),
        ]))

        result = repository.get_ticker_info_batch_from_db(
            ["aapl", "005930.ks", "broken", "nullinfo", "zzzz"]
        )

        assert list(result.keys()) == ["AAPL", "005930.KS", "BROKEN", "NULLINFO", "ZZZZ"]
        assert result["AAPL"] == {
            "symbol": "AAPL", "currency": "USD", "company_name": "Apple",
            "exchange": "NASDAQ", "first_trade_date": "1980-12-12",
        }
        assert result["005930.KS"] == {
            "symbol": "005930.KS", "currency": "KRW", "company_name": "005930.KS",
            "exchange": "Unknown", "first_trade_date": None,
        }
        default = lambda t: {"symbol": t, "currency": "USD", "company_name": t,
                             "exchange": "Unknown", "first_trade_date": None}
        assert result["BROKEN"] == default("BROKEN")
        assert result["NULLINFO"] == default("NULLINFO")
        assert result["ZZZZ"] == default("ZZZZ")

        sql, params = engine.connection.executed[0]
        assert sql == ("SELECT ticker, info_json FROM stocks WHERE ticker IN "
                       "(:t0, :t1, :t2, :t3, :t4)")
        assert params == {"t0": "AAPL", "t1": "005930.KS", "t2": "BROKEN",
                          "t3": "NULLINFO", "t4": "ZZZZ"}

    def test_empty_input_does_not_touch_db(self, repository, monkeypatch):
        engine = _use(repository, monkeypatch, _Engine())
        assert repository.get_ticker_info_batch_from_db([]) == {}
        assert engine.opened == []

    def test_db_failure_returns_defaults_without_first_trade_date(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine(broken=True))
        assert repository.get_ticker_info_batch_from_db(["aapl"]) == {
            "AAPL": {"symbol": "AAPL", "currency": "USD", "company_name": "AAPL",
                     "exchange": "Unknown"},
        }


class TestTickerInfoSingleDefaults:
    DEFAULT = {"symbol": "AAPL", "currency": "USD", "company_name": "AAPL",
               "exchange": "Unknown", "first_trade_date": None}

    def test_unknown_ticker_returns_default(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine())
        assert repository.get_ticker_info_from_db("aapl") == self.DEFAULT

    def test_db_failure_returns_default(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine(broken=True))
        assert repository.get_ticker_info_from_db("aapl") == self.DEFAULT


class TestLoadNews:
    def test_rows_are_formatted_as_news_items(self, repository, monkeypatch):
        engine = _use(repository, monkeypatch, _Engine([
            ("FROM stock_news", [
                ("제목1", "https://a", "설명", date(2024, 3, 5), datetime(2024, 3, 5, 9)),
                ("제목2", "https://b", None, "2024-03-04", datetime(2024, 3, 5, 9)),
            ]),
        ]))

        news = repository.load_news_from_db("AAPL", max_age_hours=5)

        assert news == [
            {"title": "제목1", "link": "https://a", "description": "설명",
             "pubDate": "Tue, 05 Mar 2024 00:00:00 +0900"},
            {"title": "제목2", "link": "https://b", "description": "",
             "pubDate": "2024-03-04"},
        ]
        sql, params = engine.connection.executed[0]
        assert "ORDER BY news_date DESC, created_at DESC LIMIT 20" in sql
        assert params["ticker"] == "AAPL"
        assert isinstance(params["cutoff_time"], datetime)

    def test_no_rows_returns_none(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine())
        assert repository.load_news_from_db("AAPL") is None

    def test_db_failure_returns_none(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine(broken=True))
        assert repository.load_news_from_db("AAPL") is None


class TestSaveNews:
    def test_empty_list_does_not_touch_db(self, repository, monkeypatch):
        engine = _use(repository, monkeypatch, _Engine())
        assert repository.save_news_to_db("AAPL", []) == 0
        assert engine.opened == []

    def test_replaces_ticker_news_and_skips_bad_items(self, repository, monkeypatch):
        engine = _use(repository, monkeypatch, _Engine())
        news = [
            {"title": "T" * 600, "link": "https://a", "description": "D",
             "pubDate": "Tue, 05 Mar 2024 10:00:00 +0900"},
            {"link": "https://no-title"},  # title 없음 → 건너뜀
            {"title": "빈 설명", "description": "", "pubDate": "not a date"},
        ]

        today_before = datetime.now().date()
        saved = repository.save_news_to_db("AAPL", news)
        today_after = datetime.now().date()

        assert saved == 2
        assert engine.opened == ["begin"]
        executed = engine.connection.executed
        assert executed[0] == ("DELETE FROM stock_news WHERE ticker = :ticker", {"ticker": "AAPL"})
        inserts = [(sql, p) for sql, p in executed[1:]]
        assert len(inserts) == 2
        assert all(sql.startswith("INSERT INTO stock_news") for sql, _ in inserts)
        first, second = inserts[0][1], inserts[1][1]
        assert first["title"] == "T" * 500
        assert first["link"] == "https://a"
        assert first["description"] == "D"
        assert first["source"] == "Naver"
        # RFC 2822 시각을 로컬 시간대 날짜로 바꾼다 (10:00 +0900 = 01:00 UTC)
        assert first["news_date"] == datetime.fromtimestamp(
            datetime(2024, 3, 5, 1, 0, tzinfo=timezone.utc).timestamp()
        ).date()
        assert second["title"] == "빈 설명"
        assert second["link"] == ""
        assert second["description"] is None
        # 파싱할 수 없는 pubDate는 오늘 날짜
        assert second["news_date"] in {today_before, today_after}

    def test_db_failure_returns_zero(self, repository, monkeypatch):
        _use(repository, monkeypatch, _Engine(broken=True))
        assert repository.save_news_to_db("AAPL", [{"title": "x"}]) == 0
