"""Go 백엔드 응답과의 골든 마스터 비교 (e2e).

data/histories.json은 backtest_be_go/testdata/rust/histories.json(세 백엔드 적합성 검사의 고정 시세)
사본이고, data/go_golden.json은 같은 시세로 띄운 Go 서버(운영 기준)의 POST /api/v1/backtest 응답이다.
Python 응답은 상태 코드·키·키 순서·JSON 타입이 같고 숫자는 상대 오차 1e-9 안이어야 한다.

재생성: Go 쪽 계약이 바뀌면 적합성 검사 환경(bash scripts/conformance/run.sh python)을 띄운 채
conf-go-api에 같은 요청을 보내 go_golden.json을 다시 만든다. Python 출력으로 만들지 않는다.
"""
import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.engine.marketdata import FixtureFetcher
from app.engine.source import source
from app.main import app

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
IGNORE = {"execution_time_seconds", "timestamp"}
TOLERANCE = 1e-9

with open(os.path.join(DATA_DIR, "go_golden.json"), encoding="utf-8") as f:
    CASES = json.load(f)


def _kind(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    return type(v).__name__


def _compare(path, want, got, problems):
    if _kind(want) != _kind(got):
        problems.append(f"{path}: type go={_kind(want)} python={_kind(got)}")
        return
    if isinstance(want, dict):
        wk = [k for k in want if k not in IGNORE]
        gk = [k for k in got if k not in IGNORE]
        if wk != gk:
            problems.append(f"{path}: keys go={wk[:8]}… python={gk[:8]}…")
            return
        for k in wk:
            _compare(f"{path}.{k}", want[k], got[k], problems)
    elif isinstance(want, list):
        if len(want) != len(got):
            problems.append(f"{path}: length go={len(want)} python={len(got)}")
            return
        for i, (a, b) in enumerate(zip(want, got)):
            _compare(f"{path}[{i}]", a, b, problems)
    elif _kind(want) == "number":
        if abs(want - got) / max(1.0, abs(want)) > TOLERANCE:
            problems.append(f"{path}: go={want!r} python={got!r}")
    elif want != got:
        problems.append(f"{path}: go={want!r} python={got!r}")


@pytest.fixture(scope="module")
def client():
    fixtures = FixtureFetcher.load(os.path.join(DATA_DIR, "histories.json"))
    source.clear()
    with patch("app.engine.source.fixture_fetcher", return_value=fixtures):
        yield TestClient(app)
    source.clear()


@pytest.mark.e2e
@pytest.mark.parametrize("case", CASES, ids=[c["name"] for c in CASES])
def test_matches_go_response(client, case):
    response = client.post("/api/v1/backtest", json=case["request"])
    assert response.status_code == case["status"], response.text
    problems = []
    _compare("$", case["response"], response.json(), problems)
    assert not problems, "\n".join(problems[:20])
