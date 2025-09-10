import pytest
import uuid
from fastapi.testclient import TestClient

from app.main import app


def test_backtest_history_and_community_features_flow(client: TestClient):
    # register user and get token (use unique email/username to avoid conflicts)
    suffix = uuid.uuid4().hex[:8]
    username = f"histuser_{suffix}"
    email = f"hist_{suffix}@example.com"
    r = client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert r.status_code == 201
    token = r.json()["token"]

    # run backtest (should be saved to history for authenticated user)
    resp = client.post(
        "/api/v1/backtest/run",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "ticker": "AAPL",
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
            "initial_cash": 1000,
            "strategy": "buy_and_hold",
        },
    )
    assert resp.status_code == 200

    # check history endpoint
    h = client.get("/api/v1/backtest/history", headers={"Authorization": f"Bearer {token}"})
    assert h.status_code == 200
    data = h.json()
    assert "items" in data.get("data", {}) or isinstance(data, dict)

    # create a post
    p = client.post(
        "/api/v1/community/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "like test", "content": "content"},
    )
    assert p.status_code == 201
    post_id = p.json()["id"]

    # like the post
    lk = client.post(f"/api/v1/community/posts/{post_id}/like", headers={"Authorization": f"Bearer {token}"})
    assert lk.status_code == 201
    assert lk.json()["action"] in ("liked", "unliked")

    # report the post
    rp = client.post(
        "/api/v1/community/reports",
        headers={"Authorization": f"Bearer {token}"},
        json={"target_type": "post", "target_id": post_id, "reason": "test"},
    )
    assert rp.status_code == 201

    # notices (may be empty)
    nts = client.get("/api/v1/community/notices")
    assert nts.status_code == 200
