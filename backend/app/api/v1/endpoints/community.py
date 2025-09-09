"""
간단한 커뮤니티 게시판 API (게시글/댓글)
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import text

from ....services.yfinance_db import _get_engine
from .auth import require_user

router = APIRouter()


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


@router.get("/posts")
def list_posts(limit: int = 50, offset: int = 0):
    engine = _get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text(
            """
            SELECT p.id, p.title, LEFT(p.content, 300) AS excerpt, p.created_at,
                   u.username
            FROM posts p JOIN users u ON u.id = p.user_id
            ORDER BY p.id DESC
            LIMIT :limit OFFSET :offset
            """
        ), {"limit": limit, "offset": offset}).mappings().all()
        return {"items": rows, "limit": limit, "offset": offset}


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, authorization: Optional[str] = Header(None)):
    user_id = require_user(authorization)
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO posts (user_id, title, content) VALUES (:uid, :t, :c)"),
                     {"uid": user_id, "t": payload.title, "c": payload.content})
        post = conn.execute(text(
            "SELECT p.id, p.title, p.content, p.created_at, u.username FROM posts p JOIN users u ON u.id=p.user_id WHERE p.user_id=:uid ORDER BY p.id DESC LIMIT 1"
        ), {"uid": user_id}).mappings().first()
        return post


@router.get("/posts/{post_id}")
def get_post(post_id: int):
    engine = _get_engine()
    with engine.begin() as conn:
        post = conn.execute(text(
            "SELECT p.id, p.title, p.content, p.created_at, u.username FROM posts p JOIN users u ON u.id=p.user_id WHERE p.id=:pid"
        ), {"pid": post_id}).mappings().first()
        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        comments = conn.execute(text(
            "SELECT c.id, c.content, c.created_at, u.username FROM post_comments c JOIN users u ON u.id=c.user_id WHERE c.post_id=:pid ORDER BY c.id ASC"
        ), {"pid": post_id}).mappings().all()
        return {"post": post, "comments": comments}


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(post_id: int, payload: CommentCreate, authorization: Optional[str] = Header(None)):
    user_id = require_user(authorization)
    engine = _get_engine()
    with engine.begin() as conn:
        # ensure post exists
        exists = conn.execute(text("SELECT 1 FROM posts WHERE id=:pid"), {"pid": post_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        conn.execute(text("INSERT INTO post_comments (post_id, user_id, content) VALUES (:pid, :uid, :c)"),
                     {"pid": post_id, "uid": user_id, "c": payload.content})
        cmt = conn.execute(text(
            "SELECT c.id, c.content, c.created_at, u.username FROM post_comments c JOIN users u ON u.id=c.user_id WHERE c.post_id=:pid ORDER BY c.id DESC LIMIT 1"
        ), {"pid": post_id}).mappings().first()
        return cmt

