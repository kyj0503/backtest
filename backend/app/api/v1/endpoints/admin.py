"""
관리자 API
"""
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, status, Header
from pydantic import BaseModel, Field
from sqlalchemy import text

from ....services.yfinance_db import _get_engine
from .auth import require_user
from ....models.schemas import ReportStatus

router = APIRouter()


class NoticeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    is_pinned: bool = Field(False, description="상단 고정 여부")


class NoticeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    is_pinned: Optional[bool] = None


class ReportProcess(BaseModel):
    status: ReportStatus
    admin_memo: Optional[str] = Field(None, max_length=500)


def require_admin(authorization: Optional[str]) -> dict:
    """관리자 인증을 요구"""
    user_info = require_user(authorization)
    if not user_info.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return user_info


@router.post("/notices", status_code=status.HTTP_201_CREATED)
def create_notice(payload: NoticeCreate, authorization: Optional[str] = Header(None)):
    """공지사항 작성"""
    admin_info = require_admin(authorization)
    admin_id = admin_info["user_id"]
    
    engine = _get_engine()
    with engine.begin() as conn:
        conn.execute(text(
            """
            INSERT INTO notices (admin_id, title, content, is_pinned) 
            VALUES (:aid, :title, :content, :pinned)
            """
        ), {
            "aid": admin_id,
            "title": payload.title,
            "content": payload.content,
            "pinned": payload.is_pinned
        })
        
        notice = conn.execute(text(
            """
            SELECT n.id, n.title, n.content, n.is_pinned, n.created_at, u.username AS admin_name
            FROM notices n 
            JOIN users u ON u.id = n.admin_id
            WHERE n.admin_id = :aid AND n.is_deleted = 0
            ORDER BY n.id DESC LIMIT 1
            """
        ), {"aid": admin_id}).mappings().first()
        
        return notice


@router.put("/notices/{notice_id}")
def update_notice(
    notice_id: int, 
    payload: NoticeUpdate, 
    authorization: Optional[str] = Header(None)
):
    """공지사항 수정"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        # 공지사항 존재 확인
        notice = conn.execute(text(
            "SELECT 1 FROM notices WHERE id = :nid AND is_deleted = 0"
        ), {"nid": notice_id}).fetchone()
        
        if not notice:
            raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
        
        # 업데이트할 필드 구성
        update_fields = []
        params = {"nid": notice_id}
        
        if payload.title is not None:
            update_fields.append("title = :title")
            params["title"] = payload.title
        
        if payload.content is not None:
            update_fields.append("content = :content")
            params["content"] = payload.content
        
        if payload.is_pinned is not None:
            update_fields.append("is_pinned = :pinned")
            params["pinned"] = payload.is_pinned
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="수정할 내용이 없습니다.")
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        conn.execute(text(f
            """
            UPDATE notices 
            SET {', '.join(update_fields)}
            WHERE id = :nid
            """
        ), params)
        
        # 수정된 공지사항 반환
        updated_notice = conn.execute(text(
            """
            SELECT n.id, n.title, n.content, n.is_pinned, n.created_at, n.updated_at,
                   u.username AS admin_name
            FROM notices n 
            JOIN users u ON u.id = n.admin_id
            WHERE n.id = :nid AND n.is_deleted = 0
            """
        ), {"nid": notice_id}).mappings().first()
        
        return updated_notice


@router.delete("/notices/{notice_id}")
def delete_notice(notice_id: int, authorization: Optional[str] = Header(None)):
    """공지사항 삭제 (논리적 삭제)"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        result = conn.execute(text(
            "UPDATE notices SET is_deleted = 1 WHERE id = :nid AND is_deleted = 0"
        ), {"nid": notice_id})
        
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="공지사항을 찾을 수 없습니다.")
        
        return {"status": "ok", "message": "공지사항이 삭제되었습니다."}


@router.get("/reports")
def list_reports(
    authorization: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[ReportStatus] = None
):
    """신고 목록 조회"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        # 쿼리 조건 구성
        where_conditions = []
        params = {"limit": limit, "offset": offset}
        
        if status_filter:
            where_conditions.append("r.status = :status")
            params["status"] = status_filter.value
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        rows = conn.execute(text(f
            """
            SELECT r.id, r.target_type, r.target_id, r.reason, r.status, 
                   r.created_at, r.processed_at, r.admin_memo,
                   ur.username AS reporter_name
            FROM reports r
            JOIN users ur ON ur.id = r.reporter_id
            WHERE {where_clause}
            ORDER BY r.created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ), params).mappings().all()
        
        # 전체 개수 조회
        total_count = conn.execute(text(f
            "SELECT COUNT(*) FROM reports r WHERE {where_clause}"
        ), {k: v for k, v in params.items() if k not in ['limit', 'offset']}).scalar()
        
        return {
            "items": [dict(row) for row in rows],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }


@router.put("/reports/{report_id}")
def process_report(
    report_id: int,
    payload: ReportProcess,
    authorization: Optional[str] = Header(None)
):
    """신고 처리"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        # 신고 존재 확인
        report = conn.execute(text(
            "SELECT 1 FROM reports WHERE id = :rid"
        ), {"rid": report_id}).fetchone()
        
        if not report:
            raise HTTPException(status_code=404, detail="신고를 찾을 수 없습니다.")
        
        # 신고 상태 업데이트
        conn.execute(text(
            """
            UPDATE reports 
            SET status = :status, admin_memo = :memo, processed_at = CURRENT_TIMESTAMP
            WHERE id = :rid
            """
        ), {
            "rid": report_id,
            "status": payload.status.value,
            "memo": payload.admin_memo
        })
        
        # 업데이트된 신고 정보 반환
        updated_report = conn.execute(text(
            """
            SELECT r.id, r.target_type, r.target_id, r.reason, r.status, 
                   r.created_at, r.processed_at, r.admin_memo,
                   ur.username AS reporter_name
            FROM reports r
            JOIN users ur ON ur.id = r.reporter_id
            WHERE r.id = :rid
            """
        ), {"rid": report_id}).mappings().first()
        
        return dict(updated_report)


@router.get("/stats")
def get_admin_stats(authorization: Optional[str] = Header(None)):
    """관리자 대시보드 통계"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        # 사용자 통계
        total_users = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE is_deleted = 0"
        )).scalar()
        
        new_users_today = conn.execute(text(
            "SELECT COUNT(*) FROM users WHERE DATE(created_at) = CURDATE() AND is_deleted = 0"
        )).scalar()
        
        # 게시글 통계
        total_posts = conn.execute(text(
            "SELECT COUNT(*) FROM posts WHERE is_deleted = 0"
        )).scalar()
        
        new_posts_today = conn.execute(text(
            "SELECT COUNT(*) FROM posts WHERE DATE(created_at) = CURDATE() AND is_deleted = 0"
        )).scalar()
        
        # 신고 통계
        pending_reports = conn.execute(text(
            "SELECT COUNT(*) FROM reports WHERE status = 'pending'"
        )).scalar()
        
        total_reports = conn.execute(text(
            "SELECT COUNT(*) FROM reports"
        )).scalar()
        
        # 백테스트 통계
        total_backtests = conn.execute(text(
            "SELECT COUNT(*) FROM backtest_history WHERE is_deleted = 0"
        )).scalar()
        
        backtests_today = conn.execute(text(
            "SELECT COUNT(*) FROM backtest_history WHERE DATE(created_at) = CURDATE() AND is_deleted = 0"
        )).scalar()
        
        return {
            "users": {
                "total": total_users,
                "new_today": new_users_today
            },
            "posts": {
                "total": total_posts,
                "new_today": new_posts_today
            },
            "reports": {
                "total": total_reports,
                "pending": pending_reports
            },
            "backtests": {
                "total": total_backtests,
                "today": backtests_today
            }
        }


@router.get("/users")
def list_users(
    authorization: Optional[str] = Header(None),
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None
):
    """사용자 목록 조회"""
    admin_info = require_admin(authorization)
    
    engine = _get_engine()
    with engine.begin() as conn:
        # 쿼리 조건 구성
        where_conditions = ["is_deleted = 0"]
        params = {"limit": limit, "offset": offset}
        
        if search:
            where_conditions.append("(username LIKE :search OR email LIKE :search)")
            params["search"] = f"%{search}%"
        
        where_clause = " AND ".join(where_conditions)
        
        rows = conn.execute(text(f
            """
            SELECT id, username, email, investment_type, is_admin, created_at,
                   (SELECT COUNT(*) FROM posts WHERE user_id = users.id AND is_deleted = 0) AS post_count,
                   (SELECT COUNT(*) FROM backtest_history WHERE user_id = users.id AND is_deleted = 0) AS backtest_count
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """
        ), params).mappings().all()
        
        # 전체 개수 조회
        total_count = conn.execute(text(f
            "SELECT COUNT(*) FROM users WHERE {where_clause}"
        ), {k: v for k, v in params.items() if k not in ['limit', 'offset']}).scalar()
        
        return {
            "items": [dict(row) for row in rows],
            "total_count": total_count,
            "limit": limit,
            "offset": offset
        }
