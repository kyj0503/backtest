"""
간단한 커뮤니티 게시판 API (게시글/댓글/좋아요/신고)
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import text

from ....services.yfinance_db import _get_engine
from .auth import require_user
from ....models.schemas import ReportType, ReportStatus

router = APIRouter()


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)


class ReportCreate(BaseModel):
    target_type: ReportType
    target_id: int = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=200)


@router.get("/posts")
def list_posts(limit: int = 50, offset: int = 0):
    engine = _get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text(
            """
            SELECT p.id, p.title, SUBSTR(p.content, 1, 300) AS excerpt, 
                   p.view_count, p.like_count, p.created_at, u.username
            FROM posts p 
            JOIN users u ON u.id = p.user_id
            WHERE p.is_deleted = 0 AND u.is_deleted = 0
            ORDER BY p.id DESC
            LIMIT :limit OFFSET :offset
            """
        ), {"limit": limit, "offset": offset}).mappings().all()
        return {"items": rows, "limit": limit, "offset": offset}


@router.post("/posts", status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, authorization: Optional[str] = Header(None)):
    user_info = require_user(authorization)
    user_id = user_info["user_id"]
    
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO posts (user_id, title, content) VALUES (:uid, :t, :c)"),
                     {"uid": user_id, "t": payload.title, "c": payload.content})
        post = conn.execute(text(
            """
            SELECT p.id, p.title, p.content, p.view_count, p.like_count, p.created_at, u.username 
            FROM posts p 
            JOIN users u ON u.id=p.user_id 
            WHERE p.user_id=:uid AND p.is_deleted=0
            ORDER BY p.id DESC LIMIT 1
            """
        ), {"uid": user_id}).mappings().first()
        return post


@router.get("/posts/{post_id}")
def get_post(post_id: int):
    engine = _get_engine()
    with engine.begin() as conn:
        # 조회수 증가
        conn.execute(text("UPDATE posts SET view_count = view_count + 1 WHERE id = :pid"), {"pid": post_id})
        
        post = conn.execute(text(
            """
            SELECT p.id, p.title, p.content, p.view_count, p.like_count, p.created_at, u.username 
            FROM posts p 
            JOIN users u ON u.id=p.user_id 
            WHERE p.id=:pid AND p.is_deleted=0 AND u.is_deleted=0
            """
        ), {"pid": post_id}).mappings().first()
        
        if not post:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
        comments = conn.execute(text(
            """
            SELECT c.id, c.content, c.created_at, u.username 
            FROM post_comments c 
            JOIN users u ON u.id=c.user_id 
            WHERE c.post_id=:pid AND c.is_deleted=0 AND u.is_deleted=0
            ORDER BY c.id ASC
            """
        ), {"pid": post_id}).mappings().all()
        
        return {"post": post, "comments": comments}


@router.post("/posts/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(post_id: int, payload: CommentCreate, authorization: Optional[str] = Header(None)):
    user_info = require_user(authorization)
    user_id = user_info["user_id"]
    
    engine = _get_engine()
    with engine.begin() as conn:
        # ensure post exists and is not deleted
        exists = conn.execute(text(
            "SELECT 1 FROM posts WHERE id=:pid AND is_deleted=0"
        ), {"pid": post_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
        conn.execute(text("INSERT INTO post_comments (post_id, user_id, content) VALUES (:pid, :uid, :c)"),
                     {"pid": post_id, "uid": user_id, "c": payload.content})
        
        cmt = conn.execute(text(
            """
            SELECT c.id, c.content, c.created_at, u.username 
            FROM post_comments c 
            JOIN users u ON u.id=c.user_id 
            WHERE c.post_id=:pid AND c.is_deleted=0
            ORDER BY c.id DESC LIMIT 1
            """
        ), {"pid": post_id}).mappings().first()
        return cmt


@router.post("/posts/{post_id}/like", status_code=status.HTTP_201_CREATED)
def like_post(post_id: int, authorization: Optional[str] = Header(None)):
    """게시글 좋아요/좋아요 취소"""
    user_info = require_user(authorization)
    user_id = user_info["user_id"]
    
    engine = _get_engine()
    with engine.begin() as conn:
        # ensure post exists
        exists = conn.execute(text(
            "SELECT 1 FROM posts WHERE id=:pid AND is_deleted=0"
        ), {"pid": post_id}).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
        
        # check if already liked
        liked = conn.execute(text(
            "SELECT 1 FROM post_likes WHERE post_id=:pid AND user_id=:uid"
        ), {"pid": post_id, "uid": user_id}).fetchone()
        
        if liked:
            # unlike
            conn.execute(text("DELETE FROM post_likes WHERE post_id=:pid AND user_id=:uid"),
                        {"pid": post_id, "uid": user_id})
            conn.execute(text("UPDATE posts SET like_count = like_count - 1 WHERE id=:pid"),
                        {"pid": post_id})
            action = "unliked"
        else:
            # like
            conn.execute(text("INSERT INTO post_likes (post_id, user_id) VALUES (:pid, :uid)"),
                        {"pid": post_id, "uid": user_id})
            conn.execute(text("UPDATE posts SET like_count = like_count + 1 WHERE id=:pid"),
                        {"pid": post_id})
            action = "liked"
        
        # get updated like count
        like_count = conn.execute(text("SELECT like_count FROM posts WHERE id=:pid"),
                                 {"pid": post_id}).scalar()
        
        return {"action": action, "like_count": like_count}


@router.post("/reports", status_code=status.HTTP_201_CREATED)
def create_report(payload: ReportCreate, authorization: Optional[str] = Header(None)):
    """신고 접수"""
    user_info = require_user(authorization)
    reporter_id = user_info["user_id"]
    
    engine = _get_engine()
    with engine.begin() as conn:
        # validate target exists
        if payload.target_type == ReportType.POST:
            target_exists = conn.execute(text(
                "SELECT 1 FROM posts WHERE id=:tid AND is_deleted=0"
            ), {"tid": payload.target_id}).fetchone()
        elif payload.target_type == ReportType.COMMENT:
            target_exists = conn.execute(text(
                "SELECT 1 FROM post_comments WHERE id=:tid AND is_deleted=0"
            ), {"tid": payload.target_id}).fetchone()
        elif payload.target_type == ReportType.USER:
            target_exists = conn.execute(text(
                "SELECT 1 FROM users WHERE id=:tid AND is_deleted=0"
            ), {"tid": payload.target_id}).fetchone()
        else:
            raise HTTPException(status_code=400, detail="잘못된 신고 대상 타입입니다.")
        
        if not target_exists:
            raise HTTPException(status_code=404, detail="신고 대상을 찾을 수 없습니다.")
        
        # check if already reported
        already_reported = conn.execute(text(
            """
            SELECT 1 FROM reports 
            WHERE reporter_id=:rid AND target_type=:tt AND target_id=:tid
            """
        ), {"rid": reporter_id, "tt": payload.target_type.value, "tid": payload.target_id}).fetchone()
        
        if already_reported:
            raise HTTPException(status_code=409, detail="이미 신고한 대상입니다.")
        
        conn.execute(text(
            """
            INSERT INTO reports (reporter_id, target_type, target_id, reason) 
            VALUES (:rid, :tt, :tid, :reason)
            """
        ), {
            "rid": reporter_id, 
            "tt": payload.target_type.value, 
            "tid": payload.target_id, 
            "reason": payload.reason
        })
        
        return {"status": "ok", "message": "신고가 접수되었습니다."}


@router.get("/notices")
def list_notices(limit: int = 20, offset: int = 0):
    """공지사항 목록 조회"""
    engine = _get_engine()
    with engine.begin() as conn:
        rows = conn.execute(text(
            """
            SELECT n.id, n.title, SUBSTR(n.content, 1, 300) AS excerpt, 
                   n.is_pinned, n.created_at, u.username AS admin_name
            FROM notices n 
            JOIN users u ON u.id = n.admin_id
            WHERE n.is_deleted = 0
            ORDER BY n.is_pinned DESC, n.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ), {"limit": limit, "offset": offset}).mappings().all()
        return {"items": rows, "limit": limit, "offset": offset}


@router.get("/notices/{notice_id}")
def get_notice(notice_id: int):
    """공지사항 상세 조회"""
    engine = _get_engine()
    with engine.begin() as conn:
        notice = conn.execute(text(
            """
            SELECT n.id, n.title, n.content, n.is_pinned, n.created_at, n.updated_at,
                   u.username AS admin_name
            FROM notices n 
            JOIN users u ON u.id = n.admin_id
            WHERE n.id=:nid AND n.is_deleted=0
            """
        ), {"nid": notice_id}).mappings().first()
        
        if not notice:
            raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
        
        return notice
