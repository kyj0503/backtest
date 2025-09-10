import os
import tempfile
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app


@pytest.fixture(scope="session")
def sqlite_engine():
    db_path = os.path.join(tempfile.gettempdir(), "authcomm.db")
    # ensure old temp DB removed so schema changes are applied
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    engine = create_engine(f"sqlite:///{db_path}", future=True)
    with engine.begin() as conn:
                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT NOT NULL UNIQUE,
                            email TEXT NOT NULL UNIQUE,
                            password_hash BLOB NOT NULL,
                            password_salt BLOB NOT NULL,
                            password_algo TEXT NOT NULL,
                            investment_type TEXT DEFAULT 'balanced',
                            is_admin INTEGER DEFAULT 0,
                            profile_image_url TEXT,
                            is_deleted INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                ))
                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS user_sessions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            token TEXT NOT NULL UNIQUE,
                            user_agent TEXT,
                            ip_address TEXT,
                            is_deleted INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            expires_at TEXT,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))
                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS posts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            view_count INTEGER DEFAULT 0,
                            like_count INTEGER DEFAULT 0,
                            is_deleted INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))
                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS post_comments (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            post_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            content TEXT NOT NULL,
                            is_deleted INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))

                # likes, reports, notices, backtest_history
                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS post_likes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            post_id INTEGER NOT NULL,
                            user_id INTEGER NOT NULL,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))

                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS reports (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            reporter_id INTEGER NOT NULL,
                            target_type TEXT NOT NULL,
                            target_id INTEGER NOT NULL,
                            reason TEXT,
                            status TEXT DEFAULT 'pending',
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(reporter_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))

                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS notices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            admin_id INTEGER NOT NULL,
                            title TEXT NOT NULL,
                            content TEXT NOT NULL,
                            is_pinned INTEGER DEFAULT 0,
                            is_deleted INTEGER DEFAULT 0,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(admin_id) REFERENCES users(id) ON DELETE CASCADE
                        )
                        """
                ))

                conn.execute(text(
                        """
                        CREATE TABLE IF NOT EXISTS backtest_history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            ticker TEXT,
                            strategy_name TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            initial_cash REAL,
                            final_value REAL,
                            total_return REAL,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
                        )
                        """
                ))
    return engine


@pytest.fixture(autouse=True)
def patch_engines(monkeypatch, sqlite_engine):
    from app.api.v1.endpoints import auth as auth_ep
    from app.api.v1.endpoints import community as comm_ep
    from app.api.v1.endpoints import chat as chat_ep

    def _get_engine_sqlite():
        return sqlite_engine

    monkeypatch.setattr(auth_ep, "_get_engine", _get_engine_sqlite, raising=True)
    monkeypatch.setattr(comm_ep, "_get_engine", _get_engine_sqlite, raising=True)
    monkeypatch.setattr(chat_ep, "_get_engine", _get_engine_sqlite, raising=True)


@pytest.fixture
def client():
    return TestClient(app)


def test_register_login_post_comment_flow(client):
    email = "user1@example.com"
    # register
    r = client.post("/api/v1/auth/register", json={"username": "user1", "email": email, "password": "password123"})
    assert r.status_code == 201
    token = r.json()["token"]

    # create post
    rp = client.post("/api/v1/community/posts", headers={"Authorization": f"Bearer {token}"}, json={"title": "첫 글", "content": "내용입니다"})
    assert rp.status_code == 201
    post_id = rp.json()["id"]

    # list
    lst = client.get("/api/v1/community/posts").json()
    assert any(it["id"] == post_id for it in lst["items"])

    # detail
    detail = client.get(f"/api/v1/community/posts/{post_id}").json()
    assert detail["post"]["title"] == "첫 글"

    # add comment
    rc = client.post(f"/api/v1/community/posts/{post_id}/comments", headers={"Authorization": f"Bearer {token}"}, json={"content": "댓글!"})
    assert rc.status_code == 201

    # logout
    lg = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert lg.status_code == 200

    # using same token should fail
    rp2 = client.post("/api/v1/community/posts", headers={"Authorization": f"Bearer {token}"}, json={"title": "둘째 글", "content": "x"})
    assert rp2.status_code == 401


def test_get_current_user_endpoint(client):
    r = client.post("/api/v1/auth/register", json={"username": "meuser", "email": "me@example.com", "password": "password123"})
    assert r.status_code == 201
    token = r.json()["token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    data = me.json()
    assert data["email"] == "me@example.com"
    assert data["username"] == "meuser"


def test_chat_websocket_with_fake_redis(monkeypatch, client):
    # register to get token
    r = client.post("/api/v1/auth/register", json={"username": "chatter", "email": "c@example.com", "password": "password123"})
    token = r.json()["token"]

    # fake redis
    import asyncio

    class FakePubSub:
        def __init__(self, queue):
            self.queue = queue
        async def subscribe(self, channel):
            return True
        async def unsubscribe(self, channel):
            return True
        async def close(self):
            return True
        async def listen(self):
            while True:
                data = await self.queue.get()
                yield {"type": "message", "data": data}

    class FakeRedis:
        def __init__(self):
            self.queue = asyncio.Queue()
        def pubsub(self):
            return FakePubSub(self.queue)
        async def publish(self, channel, data):
            await self.queue.put(data)
        async def close(self):
            return True

    from app.api.v1.endpoints import chat as chat_ep
    fake = FakeRedis()
    monkeypatch.setattr(chat_ep, "aioredis", type("M", (), {"from_url": staticmethod(lambda url, decode_responses=True: fake)}), raising=True)

    with client.websocket_connect(f"/api/v1/chat/ws/test?token={token}") as ws:
        ws.send_text("hello")
        found = False
        for _ in range(5):
            msg = ws.receive_text()
            if 'hello' in msg:
                found = True
                break
        assert found
