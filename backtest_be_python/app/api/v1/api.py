"""
API v1 라우터

**역할**:
- FastAPI의 APIRouter를 사용하여 v1 API 엔드포인트 관리
- 백테스트 관련 모든 엔드포인트를 하나의 라우터로 구성

**엔드포인트**:
- POST /api/v1/backtest: 계산 실행 (기존 include_* 통합 응답도 지원)
- GET /api/v1/prices, /exchange-rates, /benchmarks, /news: 독립 조회·재시도
- 전략 목록은 프론트엔드에서 관리
- 콘솔은 계산을 먼저 표시하고 참고 데이터를 별도로 조회한다.
"""
from fastapi import APIRouter
from .endpoints import backtest, market_data

api_router = APIRouter()

# 백테스팅 API (통합 엔드포인트)
api_router.include_router(
    backtest.router,
    prefix="/backtest",
    tags=["백테스팅"]
)

api_router.include_router(market_data.router, tags=["시장 데이터"])

