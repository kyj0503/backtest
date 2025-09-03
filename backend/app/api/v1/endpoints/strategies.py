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


@router.get(
    "/{strategy_name}",
    response_model=StrategyInfo,
    summary="특정 전략 정보 조회",
    description="지정된 전략의 상세 정보를 반환합니다."
)
async def get_strategy_info(strategy_name: str):
    """
    특정 전략 정보 조회 API
    
    Args:
        strategy_name: 조회할 전략명
        
    Returns:
        전략의 상세 정보 (파라미터, 설명 등)
    """
    try:
        strategy_info = strategy_service.get_strategy_info(strategy_name)
        
        return StrategyInfo(
            name=strategy_name,
            description=strategy_info['description'],
            parameters=strategy_info['parameters']
        )
        
    except ValueError as e:
        logger.error(f"전략 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"전략 정보 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="전략 정보 조회 중 오류가 발생했습니다."
        )


@router.get(
    "/{strategy_name}/validate",
    summary="전략 파라미터 유효성 검증",
    description="주어진 파라미터가 전략에 유효한지 검증합니다."
)
async def validate_strategy_params(strategy_name: str, **params):
    """
    전략 파라미터 유효성 검증 API
    
    Args:
        strategy_name: 검증할 전략명
        **params: 검증할 파라미터들 (쿼리 파라미터로 전달)
        
    Returns:
        검증 결과와 유효한 파라미터 값들
    """
    try:
        validated_params = strategy_service.validate_strategy_params(
            strategy_name, dict(params)
        )
        
        return {
            "strategy": strategy_name,
            "is_valid": True,
            "validated_params": validated_params,
            "message": "파라미터가 유효합니다."
        }
        
    except ValueError as e:
        return {
            "strategy": strategy_name,
            "is_valid": False,
            "error": str(e),
            "message": "파라미터 검증에 실패했습니다."
        }
    except Exception as e:
        logger.error(f"파라미터 검증 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파라미터 검증 중 오류가 발생했습니다."
        ) 