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

from fastapi import APIRouter, HTTPException, status, Header, Request
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import text

from ....services.yfinance_db import _get_engine
from ....models.schemas import InvestmentType

router = APIRouter()


def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = secrets.token_bytes(32)  # 32바이트로 증가
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return dk, salt


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    investment_type: Optional[InvestmentType] = Field(InvestmentType.BALANCED, description="투자 성향")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: int
    username: str
    email: EmailStr
    investment_type: InvestmentType
    is_admin: bool = False


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, request: Request):
    engine = _get_engine()
    with engine.begin() as conn:
        # uniqueness check
        exists = conn.execute(text("SELECT 1 FROM users WHERE email=:e OR username=:u"), {"e": req.email, "u": req.username}).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="이미 사용 중인 이메일 또는 사용자명입니다.")

        pw_hash, pw_salt = _hash_password(req.password)
        ins = text(
            """
            INSERT INTO users (username, email, password_hash, password_salt, password_algo, investment_type)
            VALUES (:u, :e, :h, :s, 'pbkdf2_sha256', :inv_type)
            """
        )
        conn.execute(ins, {
            "u": req.username, 
            "e": req.email, 
            "h": pw_hash, 
            "s": pw_salt,
            "inv_type": req.investment_type.value
        })
        row = conn.execute(text("SELECT id, investment_type FROM users WHERE email=:e"), {"e": req.email}).fetchone()
        user_id = int(row[0])
        investment_type = row[1]

        # create session token (7 days)
        token = secrets.token_hex(64)  # 더 긴 토큰
        expires = datetime.utcnow() + timedelta(days=7)
        
        # 클라이언트 정보 수집
        user_agent = request.headers.get("user-agent", "")[:255]  # 255자 제한
        ip_address = request.client.host if request.client else None
        
        conn.execute(text(
            """
            INSERT INTO user_sessions (user_id, token, user_agent, ip_address, expires_at) 
            VALUES (:uid, :t, :ua, :ip, :exp)
            """
        ), {
            "uid": user_id, 
            "t": token, 
            "ua": user_agent,
            "ip": ip_address,
            "exp": expires
        })

        return AuthResponse(
            token=token, 
            user_id=user_id, 
            username=req.username, 
            email=req.email,
            investment_type=InvestmentType(investment_type),
            is_admin=False
        )


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, request: Request):
    engine = _get_engine()
    with engine.begin() as conn:
        row = conn.execute(text(
            "SELECT id, username, email, password_hash, password_salt, investment_type, is_admin FROM users WHERE email=:e AND is_deleted=0"
        ), {"e": req.email}).fetchone()
        if not row:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        
        user_id, username, email, pw_hash_db, pw_salt, investment_type, is_admin = (
            int(row[0]), row[1], row[2], row[3], row[4], row[5], bool(row[6])
        )
        
        calc_hash, _ = _hash_password(req.password, pw_salt)
        if not hmac.compare_digest(calc_hash, pw_hash_db):
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")

        token = secrets.token_hex(64)
        expires = datetime.utcnow() + timedelta(days=7)
        
        # 클라이언트 정보 수집
        user_agent = request.headers.get("user-agent", "")[:255]
        ip_address = request.client.host if request.client else None
        
        conn.execute(text(
            """
            INSERT INTO user_sessions (user_id, token, user_agent, ip_address, expires_at) 
            VALUES (:uid, :t, :ua, :ip, :exp)
            """
        ), {
            "uid": user_id, 
            "t": token,
            "ua": user_agent,
            "ip": ip_address,
            "exp": expires
        })
        
        return AuthResponse(
            token=token, 
            user_id=user_id, 
            username=username, 
            email=email,
            investment_type=InvestmentType(investment_type),
            is_admin=is_admin
        )


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    # 논리적 삭제로 변경
    if not authorization or not authorization.lower().startswith('bearer '):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = authorization.split(' ', 1)[1]
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text("UPDATE user_sessions SET is_deleted=1 WHERE token=:t"), {"t": token})
    return {"status": "ok"}


def require_user(authorization: Optional[str]) -> dict:
    """사용자 인증을 요구하고 사용자 정보를 반환"""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = authorization.split(" ", 1)[1]
    engine = _get_engine()
    with engine.begin() as conn:
        row = conn.execute(text(
            """
            SELECT s.user_id, s.expires_at, u.username, u.email, u.is_admin, u.investment_type
            FROM user_sessions s 
            JOIN users u ON u.id = s.user_id 
            WHERE s.token=:t AND s.is_deleted=0 AND u.is_deleted=0
            """
        ), {"t": token}).fetchone()
        
        if not row:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")
        
        user_id, expires, username, email, is_admin, investment_type = (
            int(row[0]), row[1], row[2], row[3], bool(row[4]), row[5]
        )
        
        # SQLite에서는 문자열로 반환될 수 있음
        if isinstance(expires, str):
            try:
                expires = datetime.fromisoformat(expires)
            except Exception:
                expires = None
        if expires and datetime.utcnow() > expires:
            raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
        
        return {
            "user_id": user_id,
            "username": username,
            "email": email,
            "is_admin": is_admin,
            "investment_type": investment_type
        }
