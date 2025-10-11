"""
API v1 라우터

**역할**:
- FastAPI의 APIRouter를 사용하여 v1 API 엔드포인트 관리
- 백테스트 관련 모든 엔드포인트를 하나의 라우터로 구성

**엔드포인트**:
- POST /api/v1/backtest: 백테스트 실행 및 필요한 모든 데이터 응답
- 전략 목록은 프론트엔드에서 관리
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

