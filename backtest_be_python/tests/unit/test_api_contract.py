"""Public request/response schemas captured before the infrastructure migration."""
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from app.main import app

pytestmark = pytest.mark.unit
DOCUMENTATION = {"description", "summary", "example", "examples", "title", "tags", "externalDocs"}

def _contract(value):
    if isinstance(value, dict):
        return {key: _contract(child) for key, child in value.items() if key not in DOCUMENTATION}
    if isinstance(value, list):
        return [_contract(child) for child in value]
    return value

def test_preserves_production_routes_requests_and_responses():
    expected = json.loads((Path(__file__).parent / "fixtures/api-contract.json").read_text(encoding="utf-8"))
    with TestClient(app) as http:
        app.openapi_schema = None
        response = http.get("/api/v1/openapi.json")
        assert response.status_code == 200
        actual = response.json()
    # The independently retriable read API is additive. Every pre-existing
    # route and request/response schema must remain byte-for-byte equivalent.
    reads = {'/api/v1/' + name for name in ('prices', 'exchange-rates', 'benchmarks', 'news')}
    assert set(actual['paths']) == set(expected['paths']) | reads
    for path in reads:
        assert 'get' in actual['paths'].pop(path)
    # Only the calculation's verification header/403 response are additive.
    post = actual['paths']['/api/v1/backtest']['post']
    header = post.pop('parameters')
    assert len(header) == 1
    assert header[0]['name'] == 'X-Turnstile-Token'
    assert header[0]['in'] == 'header' and header[0]['required'] is False
    assert set(post['responses'].pop('403')) == {'description'}
    for section in ("paths", "components"):
        assert _contract(actual[section]) == expected[section]
