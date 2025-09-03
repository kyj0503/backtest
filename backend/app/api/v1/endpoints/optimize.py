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


@router.get(
    "/targets",
    summary="최적화 가능한 지표 목록",
    description="최적화 대상으로 사용할 수 있는 성능 지표들의 목록을 반환합니다."
)
async def get_optimization_targets():
    """
    최적화 대상 지표 목록 API
    
    백테스트 결과에서 최적화 대상으로 사용할 수 있는 지표들을 반환합니다.
    """
    try:
        targets = {
            "SQN": {
                "name": "System Quality Number",
                "description": "시스템 품질 지수 - 전략의 전반적 품질을 나타냄",
                "higher_better": True
            },
            "Return [%]": {
                "name": "Total Return",
                "description": "총 수익률",
                "higher_better": True
            },
            "Sharpe Ratio": {
                "name": "Sharpe Ratio",
                "description": "샤프 비율 - 위험 대비 수익률",
                "higher_better": True
            },
            "Sortino Ratio": {
                "name": "Sortino Ratio",
                "description": "소르티노 비율 - 하방 위험 대비 수익률",
                "higher_better": True
            },
            "Calmar Ratio": {
                "name": "Calmar Ratio",
                "description": "칼마 비율 - 최대 손실 대비 연간 수익률",
                "higher_better": True
            },
            "Profit Factor": {
                "name": "Profit Factor",
                "description": "수익 팩터 - 총 이익 대비 총 손실",
                "higher_better": True
            },
            "Win Rate [%]": {
                "name": "Win Rate",
                "description": "승률 - 수익 거래 비율",
                "higher_better": True
            },
            "Max. Drawdown [%]": {
                "name": "Maximum Drawdown",
                "description": "최대 손실률 (음수)",
                "higher_better": False
            }
        }
        
        return {
            "targets": targets,
            "default": "SQN",
            "recommended": ["SQN", "Sharpe Ratio", "Calmar Ratio"]
        }
        
    except Exception as e:
        logger.error(f"최적화 대상 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 대상 조회 중 오류가 발생했습니다."
        )


@router.get(
    "/methods",
    summary="사용 가능한 최적화 방법 목록",
    description="파라미터 최적화에 사용할 수 있는 방법들의 목록을 반환합니다."
)
async def get_optimization_methods():
    """
    최적화 방법 목록 API
    
    사용 가능한 최적화 알고리즘들의 정보를 반환합니다.
    """
    try:
        methods = {
            "grid": {
                "name": "Grid Search",
                "description": "격자 탐색 - 모든 파라미터 조합을 체계적으로 테스트",
                "pros": ["완전 탐색", "재현 가능", "이해하기 쉬움"],
                "cons": ["계산 시간이 많이 소요", "파라미터 개수에 민감"],
                "best_for": "파라미터 개수가 적고 정확한 결과가 필요한 경우"
            },
            "sambo": {
                "name": "SAMBO Optimization",
                "description": "모델 기반 최적화 - 베이지안 최적화 알고리즘",
                "pros": ["빠른 수렴", "효율적", "고차원 파라미터 처리 가능"],
                "cons": ["확률적 결과", "복잡한 알고리즘"],
                "best_for": "파라미터 개수가 많거나 빠른 결과가 필요한 경우"
            }
        }
        
        return {
            "methods": methods,
            "default": "grid",
            "recommended": "sambo"
        }
        
    except Exception as e:
        logger.error(f"최적화 방법 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="최적화 방법 조회 중 오류가 발생했습니다."
        ) 