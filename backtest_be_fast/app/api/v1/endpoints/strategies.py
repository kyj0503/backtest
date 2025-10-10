"""
전략 관리 API
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Dict, Any
from ....models.responses import StrategyInfo, StrategyListResponse
from ....services.strategy_service import strategy_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/",
    response_model=StrategyListResponse,
    summary="사용 가능한 전략 목록 조회",
    description="백테스팅에 사용할 수 있는 모든 전략의 목록과 정보를 반환합니다."
)
async def get_strategies():
    """
    전략 목록 조회 API
    
    사용 가능한 모든 백테스팅 전략의 정보를 반환합니다.
    각 전략에 대해 다음 정보를 제공합니다:
    - 전략명과 설명
    - 사용 가능한 파라미터
    - 파라미터별 타입, 기본값, 범위
    """
    try:
        strategies_data = strategy_service.get_all_strategies()
        
        strategies = []
        for strategy_key, strategy_info in strategies_data.items():
            strategies.append(StrategyInfo(
                name=strategy_key,
                description=strategy_info['description'],
                parameters=strategy_info['parameters']
            ))
        
        return StrategyListResponse(
            strategies=strategies,
            total_count=len(strategies)
        )
        
    except Exception as e:
        logger.error(f"전략 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전략 목록 조회 중 오류가 발생했습니다."
        )


