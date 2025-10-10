"""
백테스팅 최적화 API
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from ....models.requests import OptimizationRequest
from ....models.responses import OptimizationResult
from ....services.backtest_service import backtest_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/run",
    response_model=OptimizationResult,
    status_code=status.HTTP_200_OK,
    summary="전략 파라미터 최적화 실행",
    description="주어진 전략의 파라미터를 최적화하여 최고 성능을 찾습니다."
)
async def run_optimization(request: OptimizationRequest):
    """
    전략 파라미터 최적화 API
    
    - **ticker**: 주식 티커 심볼 (예: AAPL, GOOGL)
    - **start_date**: 백테스트 시작 날짜 (YYYY-MM-DD)
    - **end_date**: 백테스트 종료 날짜 (YYYY-MM-DD)
    - **initial_cash**: 초기 투자금액
    - **strategy**: 최적화할 전략명
    - **param_ranges**: 파라미터별 최적화 범위 (예: {"short_window": [5, 15]})
    - **method**: 최적화 방법 ("grid" 또는 "sambo")
    - **maximize**: 최적화할 지표 (기본값: "SQN")
    - **max_tries**: 최대 시도 횟수
    """
    try:
        logger.info(f"최적화 API 시작: {request.ticker}, {request.strategy}")
        
        # 최적화 실행
        result = await backtest_service.optimize_strategy(request)
        
        logger.info(f"최적화 API 완료: {request.ticker}")
        return result
        
    except ValueError as e:
        logger.error(f"최적화 요청 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"최적화 실행 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 실행 중 오류가 발생했습니다."
        )


