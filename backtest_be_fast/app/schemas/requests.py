"""
API 요청 모델 정의

**Phase 2.3 리팩터링 변경사항**:
- Pydantic schemas는 타입 검증과 파싱만 담당
- 비즈니스 로직 검증은 app/validators로 이동
- Field 제약조건(gt, ge, le 등)은 FastAPI 문서 생성을 위해 유지
- field_validator는 타입 변환과 기본 포맷 검증만 수행
- 복잡한 비즈니스 규칙은 BacktestValidator, PortfolioValidator에서 처리
"""
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from ..core.config import settings


class StrategyType(str, Enum):
    """지원되는 전략 타입"""
    SMA_STRATEGY = "sma_strategy"
    RSI_STRATEGY = "rsi_strategy"
    BOLLINGER_STRATEGY = "bollinger_strategy"
    MACD_STRATEGY = "macd_strategy"
    BUY_HOLD_STRATEGY = "buy_hold_strategy"
    EMA_STRATEGY = "ema_strategy"


class BacktestRequest(BaseModel):
    """백테스트 요청 모델"""
    ticker: str = Field(..., description="주식 티커 심볼 (예: AAPL, GOOGL)")
    start_date: Union[date, str] = Field(..., description="백테스트 시작 날짜")
    end_date: Union[date, str] = Field(..., description="백테스트 종료 날짜")
    initial_cash: float = Field(default=10000.0, gt=0, description="초기 투자금액")
    strategy: StrategyType = Field(..., description="사용할 전략")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="전략 파라미터")
    commission: float = Field(default=0.002, ge=0, le=0.1, description="거래 수수료 (소수점)")
    spread: float = Field(default=0.0, ge=0, description="스프레드")
    benchmark_ticker: Optional[str] = Field(default=None, description="비교 벤치마크 티커 (예: MSFT, SPY)")
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """날짜 파싱 (타입 변환)"""
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('날짜 형식은 YYYY-MM-DD여야 합니다')
        return v

    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        """
        기본 날짜 순서 검증 (FastAPI 조기 검증용)

        Note: 상세한 비즈니스 로직 검증(기간 제한, 미래 날짜 등)은
        BacktestValidator에서 수행됨
        """
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('종료 날짜는 시작 날짜보다 이후여야 합니다')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "initial_cash": 10000.0,
                "strategy": "sma_crossover",
                "strategy_params": {
                    "short_window": 10,
                    "long_window": 20
                },
                "commission": 0.002,
                "benchmark_ticker": "MSFT"
            }
        }
