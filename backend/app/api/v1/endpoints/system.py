"""
시스템 정보 API 엔드포인트
"""
from fastapi import APIRouter
from datetime import datetime, timezone
import os
from pathlib import Path
import pytz

router = APIRouter()

# 서버 시작 시간 저장 (UTC)
SERVER_START_TIME = datetime.now(timezone.utc)

def get_version():
    """애플리케이션 버전 정보 가져오기"""
    try:
        # 환경 변수에서 버전 정보를 가져오거나 기본값 사용
        version = os.getenv("APP_VERSION", "1.0.0")
        return version
    except Exception:
        return "unknown"

def get_git_info():
    """Git 정보 가져오기 (선택적)"""
    try:
        # Docker 환경에서는 .git 폴더가 없을 수 있으므로 환경변수 사용
        git_commit = os.getenv("GIT_COMMIT", "unknown")
        git_branch = os.getenv("GIT_BRANCH", "unknown")
        return {
            "commit": git_commit[:8] if git_commit != "unknown" else "unknown",  # 짧은 커밋 해시
            "branch": git_branch
        }
    except Exception:
        return {
            "commit": "unknown",
            "branch": "unknown"
        }

@router.get("/info", summary="서버 정보")
async def get_server_info():
    """
    서버 버전 및 시간 정보를 반환합니다.
    
    Returns:
        dict: 서버 정보 (버전, 시작 시간, 업타임 등)
    """
    current_time_utc = datetime.now(timezone.utc)
    uptime = current_time_utc - SERVER_START_TIME
    git_info = get_git_info()
    
    # KST 시간대 설정
    kst = pytz.timezone('Asia/Seoul')
    server_start_kst = SERVER_START_TIME.astimezone(kst)
    current_time_kst = current_time_utc.astimezone(kst)
    
    return {
        "version": get_version(),
        "git": git_info,
        "start_time": SERVER_START_TIME.isoformat(),  # UTC 원본
        "start_time_kst": server_start_kst.isoformat(),  # KST 변환
        "current_time": current_time_utc.isoformat(),  # UTC 원본
        "current_time_kst": current_time_kst.isoformat(),  # KST 변환
        "timezone": {
            "server": str(SERVER_START_TIME.tzinfo),
            "display": "Asia/Seoul"
        },
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": str(uptime).split('.')[0],  # 마이크로초 제거
        "environment": os.getenv("ENVIRONMENT", "development"),
        "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        "platform": os.sys.platform,
        "hostname": os.getenv("HOSTNAME", "unknown")
    }

@router.get("/health", summary="헬스 체크")
async def health_check():
    """
    서버 상태 확인을 위한 헬스 체크 엔드포인트
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
