"""Human verification must reject before reserving a slot or doing data I/O."""
import json
from unittest.mock import Mock
import urllib.error

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app.main import app
from app.api.v1 import turnstile
from app.api.v1.endpoints import backtest
from app.core.config import Settings

pytestmark = pytest.mark.unit
PAYLOAD = {"portfolio": [{"symbol": "AAPL", "amount": 1000}],
           "start_date": "2023-01-01", "end_date": "2023-12-31", "strategy": "buy_hold_strategy"}
GOOD = {"success": True, "hostname": "backtest.yeonjae.kr", "action": "backtest"}


@pytest.fixture
def gate(monkeypatch):
    for name, value in {"turnstile_enabled": True, "turnstile_secret_key": SecretStr("test-only-secret"),
                        "turnstile_allowed_hostnames": "backtest.yeonjae.kr",
                        "turnstile_expected_action": "backtest"}.items():
        monkeypatch.setattr(turnstile.settings, name, value)
    verifier = Mock(return_value=GOOD)
    runner_factory = Mock()
    repository = Mock()
    monkeypatch.setattr(turnstile, "_siteverify", verifier)
    monkeypatch.setattr(backtest, "get_backtest_runner", runner_factory)
    monkeypatch.setattr(backtest, "get_stock_repository", repository)
    return verifier, runner_factory, repository


def test_enabled_by_default_and_secret_repr_redacted(monkeypatch):
    monkeypatch.delenv("TURNSTILE_ENABLED")
    settings = Settings(_env_file=None, turnstile_secret_key="not-a-real-secret")
    assert settings.turnstile_enabled is True
    assert "not-a-real-secret" not in repr(settings)


@pytest.mark.parametrize("headers", [{}, {"X-Turnstile-Token": ""}, {"X-Turnstile-Token": " "},
    {"X-Turnstile-Token": "a" * 2049}, [("X-Turnstile-Token", "one"), ("X-Turnstile-Token", "two")]])
def test_missing_malformed_tokens_do_not_verify_or_start_work(gate, headers):
    response = TestClient(app).post("/api/v1/backtest", json=PAYLOAD, headers=headers)
    assert response.status_code == 403
    for mock in gate:
        mock.assert_not_called()


@pytest.mark.parametrize("result", [
    {"success": False, "error-codes": ["invalid-input-response"]},
    {"success": False, "error-codes": ["timeout-or-duplicate"]},
    {**GOOD, "success": "true"}, {**GOOD, "hostname": "evil.example"},
    {**GOOD, "hostname": "backtest.yeonjae.kr.evil.example"},
    {**GOOD, "action": "login"}, {"success": True}, {**GOOD, "hostname": []},
])
def test_invalid_expired_replayed_or_wrong_scope_tokens_never_start_work(gate, result):
    verifier, runner, repository = gate
    verifier.return_value = result
    response = TestClient(app).post("/api/v1/backtest", json=PAYLOAD,
                                  headers={"X-Turnstile-Token": "opaque-token", "Host": "evil.example"})
    assert response.status_code == 403
    verifier.assert_called_once_with("opaque-token", "test-only-secret")
    runner.assert_not_called()
    repository.assert_not_called()


@pytest.mark.parametrize("error", [TimeoutError("secret should not leak"),
    urllib.error.URLError("secret should not leak"), ValueError("secret should not leak")])
def test_outage_is_fail_closed_and_does_not_leak_details(gate, error):
    verifier, runner, repository = gate
    verifier.side_effect = error
    response = TestClient(app).post("/api/v1/backtest", json=PAYLOAD, headers={"X-Turnstile-Token": "token"})
    assert response.status_code == 503
    assert "secret" not in response.text
    runner.assert_not_called()
    repository.assert_not_called()


@pytest.mark.parametrize("name,value", [("turnstile_secret_key", SecretStr("")),
    ("turnstile_allowed_hostnames", ""), ("turnstile_expected_action", "")])
def test_missing_configuration_does_not_bypass(gate, monkeypatch, name, value):
    monkeypatch.setattr(turnstile.settings, name, value)
    assert TestClient(app).post("/api/v1/backtest", json=PAYLOAD,
        headers={"X-Turnstile-Token": "token"}).status_code == 503
    for mock in gate:
        mock.assert_not_called()


def test_valid_token_is_checked_before_existing_runner_and_replay_rejected(gate):
    verifier, factory, repository = gate
    class Runner:
        async def run(self, work, **kwargs):
            verifier.assert_called_once()
            return {"status": "success", "data": {"calculation": "existing-result"}}
    factory.return_value = Runner()
    http = TestClient(app)
    headers = {"X-Turnstile-Token": "single-use-token"}
    first = http.post("/api/v1/backtest", json=PAYLOAD, headers=headers)
    assert first.status_code == 200
    verifier.return_value = {"success": False, "error-codes": ["timeout-or-duplicate"]}
    assert http.post("/api/v1/backtest", json=PAYLOAD, headers=headers).status_code == 403
    factory.assert_called_once()
    repository.assert_not_called()


@pytest.mark.parametrize("path", ["prices", "exchange-rates", "benchmarks", "news"])
def test_read_routes_do_not_require_verification(gate, path):
    # Missing required query -> existing schema validation, not a human challenge.
    assert TestClient(app).get("/api/v1/" + path).status_code == 422
    gate[0].assert_not_called()


def test_siteverify_uses_fixed_https_post_bounded_timeout_and_no_remoteip(monkeypatch):
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = json.dumps(GOOD).encode()
    urlopen = Mock(return_value=response)
    monkeypatch.setattr(turnstile.urllib.request, "urlopen", urlopen)
    assert turnstile._siteverify("a+token", "test-only-secret") == GOOD
    request = urlopen.call_args.args[0]
    assert request.full_url == turnstile.SITEVERIFY_URL
    assert request.get_method() == "POST"
    assert request.data == b"secret=test-only-secret&response=a%2Btoken"
    assert 0 < urlopen.call_args.kwargs["timeout"] <= 10
    response.read.assert_called_once_with(16_385)


@pytest.mark.parametrize("body", [b"not-json", b"[]", b"x" * 16_385])
def test_malformed_siteverify_payload_rejected(monkeypatch, body):
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = body
    monkeypatch.setattr(turnstile.urllib.request, "urlopen", Mock(return_value=response))
    with pytest.raises(ValueError):
        turnstile._siteverify("token", "test-only-secret")
