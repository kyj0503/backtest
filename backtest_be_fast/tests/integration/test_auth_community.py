import os
import tempfile
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from app.main import app

pytestmark = pytest.mark.integration


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


# DELETED: high-level integration test removed per request
# This file was cleared to keep only unit tests in the repository.
