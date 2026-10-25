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
    assert set(actual['paths']) == set(expected['paths']) | {'/api/v1/market-data'}
    assert 'get' in actual['paths'].pop('/api/v1/market-data')
    for section in ("paths", "components"):
        assert _contract(actual[section]) == expected[section]
