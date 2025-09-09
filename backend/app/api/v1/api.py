"""
API v1 라우터 통합
"""
from fastapi import APIRouter
from .endpoints import backtest, strategies, optimize, naver_news
from .endpoints import auth, community, chat
from .endpoints import yfinance_cache

api_router = APIRouter()

# 각 API 라우터를 메인 API 라우터에 포함
api_router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["백테스팅"]
)

api_router.include_router(
    strategies.router,
    prefix="/strategies",
    tags=["전략 관리"]
)

api_router.include_router(
    optimize.router,
    prefix="/optimize",
    tags=["최적화"]
) 

api_router.include_router(
    yfinance_cache.router,
    prefix="/yfinance",
    tags=["yfinance 캐시"]
)

api_router.include_router(
    naver_news.router,
    prefix="/naver-news",
    tags=["네이버 뉴스 검색"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["인증"]
)

api_router.include_router(
    community.router,
    prefix="/community",
    tags=["커뮤니티"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["채팅"]
)
