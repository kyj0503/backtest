"""
간단한 회원가입/로그인 API (세션 토큰 기반)
"""
import os
import base64
import hmac
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import text

from ....services.yfinance_db import _get_engine

router = APIRouter()


def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return dk, salt


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    email: EmailStr


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    engine = _get_engine()
    with engine.begin() as conn:
        # uniqueness check
        exists = conn.execute(text("SELECT 1 FROM users WHERE email=:e OR username=:u"), {"e": req.email, "u": req.username}).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="이미 사용 중인 이메일 또는 사용자명입니다.")

        pw_hash, pw_salt = _hash_password(req.password)
        ins = text(
            """
            INSERT INTO users (username, email, password_hash, password_salt, password_algo)
            VALUES (:u, :e, :h, :s, 'pbkdf2_sha256')
            """
        )
        conn.execute(ins, {"u": req.username, "e": req.email, "h": pw_hash, "s": pw_salt})
        row = conn.execute(text("SELECT id FROM users WHERE email=:e"), {"e": req.email}).fetchone()
        user_id = int(row[0])

        # create session token (7 days)
        token = secrets.token_hex(32)
        expires = datetime.utcnow() + timedelta(days=7)
        conn.execute(text("INSERT INTO user_sessions (user_id, token, expires_at) VALUES (:uid, :t, :exp)"),
                     {"uid": user_id, "t": token, "exp": expires})

        return AuthResponse(token=token, user_id=user_id, username=req.username, email=req.email)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    engine = _get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT id, username, email, password_hash, password_salt FROM users WHERE email=:e"), {"e": req.email}).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        user_id, username, email, pw_hash_db, pw_salt = int(row[0]), row[1], row[2], row[3], row[4]
        calc_hash, _ = _hash_password(req.password, pw_salt)
        if not hmac.compare_digest(calc_hash, pw_hash_db):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

        token = secrets.token_hex(32)
        expires = datetime.utcnow() + timedelta(days=7)
        conn.execute(text("INSERT INTO user_sessions (user_id, token, expires_at) VALUES (:uid, :t, :exp)"),
                     {"uid": user_id, "t": token, "exp": expires})
        return AuthResponse(token=token, user_id=user_id, username=username, email=email)


def require_user(authorization: Optional[str]) -> int:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    engine = _get_engine()
    with engine.begin() as conn:
        row = conn.execute(text("SELECT user_id, expires_at FROM user_sessions WHERE token=:t"), {"t": token}).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        user_id, expires = int(row[0]), row[1]
        if expires and datetime.utcnow() > expires:
            raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
        return user_id

