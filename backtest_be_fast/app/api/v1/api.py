"""
API v1 라우터 통합

단일 엔드포인트 아키텍처:
- POST /api/v1/backtest: 백테스트 실행 및 모든 데이터 통합 응답
- 전략 목록은 프론트엔드에 하드코딩
- 주가/환율/뉴스 데이터는 백테스트 응답에 포함
"""
from fastapi import APIRouter
from .endpoints import backtest

api_router = APIRouter()

# 백테스팅 API (통합 엔드포인트)
api_router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["백테스팅"]
)

