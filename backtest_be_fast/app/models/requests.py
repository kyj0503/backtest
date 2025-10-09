"""
API 요청 모델 정의
"""
from datetime import date, datetime
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from ..core.config import settings


class StrategyType(str, Enum):
    """지원되는 전략 타입"""
    SMA_CROSSOVER = "sma_crossover"
    RSI = "rsi"
    BOLLINGER_BANDS = "bollinger_bands"
    MACD = "macd"
    BUY_AND_HOLD = "buy_and_hold"
    EMA_CROSSOVER = "ema_crossover"


class OptimizationMethod(str, Enum):
    """최적화 방법"""
    GRID = "grid"
    SAMBO = "sambo"


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
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('날짜 형식은 YYYY-MM-DD여야 합니다')
        return v
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
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


class OptimizationRequest(BaseModel):
    """파라미터 최적화 요청 모델"""
    ticker: str = Field(..., description="주식 티커 심볼")
    start_date: Union[date, str] = Field(..., description="백테스트 시작 날짜")
    end_date: Union[date, str] = Field(..., description="백테스트 종료 날짜")
    initial_cash: float = Field(default=10000.0, gt=0, description="초기 투자금액")
    strategy: StrategyType = Field(..., description="최적화할 전략")
    param_ranges: Dict[str, List[Union[int, float]]] = Field(..., description="파라미터 범위")
    method: OptimizationMethod = Field(default=OptimizationMethod.GRID, description="최적화 방법")
    maximize: str = Field(default="SQN", description="최적화할 지표")
    max_tries: Optional[int] = Field(default=settings.max_optimization_iterations, description="최대 시도 횟수")
    commission: float = Field(default=0.002, ge=0, le=0.1, description="거래 수수료")
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('날짜 형식은 YYYY-MM-DD여야 합니다')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "initial_cash": 10000.0,
                "strategy": "sma_crossover",
                "param_ranges": {
                    "short_window": [5, 15],
                    "long_window": [20, 50]
                },
                "method": "grid",
                "maximize": "SQN",
                "max_tries": 100
            }
        }


class PlotRequest(BaseModel):
    """차트 생성 요청 모델"""
    ticker: str = Field(..., description="주식 티커 심볼")
    start_date: Union[date, str] = Field(..., description="시작 날짜")
    end_date: Union[date, str] = Field(..., description="종료 날짜")
    strategy: StrategyType = Field(..., description="전략")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="전략 파라미터")
    plot_width: int = Field(default=1200, description="차트 너비")
    filename: Optional[str] = Field(default=None, description="저장할 파일명")
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('날짜 형식은 YYYY-MM-DD여야 합니다')
        return v


class PortfolioAsset(BaseModel):
    """포트폴리오 자산 모델 (통합 백테스트용)"""
    symbol: str = Field(..., min_length=1, max_length=10, description="주식 심볼 또는 자산 코드")
    amount: float = Field(..., gt=0, description="투자 금액")
    investment_type: Optional[str] = Field("lump_sum", description="투자 방식 (lump_sum, dca)")
    dca_periods: Optional[int] = Field(12, ge=1, le=60, description="분할 매수 기간")
    asset_type: Optional[str] = Field("stock", description="자산 타입 (stock, cash)")


class UnifiedBacktestRequest(BaseModel):
    """통합 백테스트 요청 모델 (단일/포트폴리오 자동 구분)"""
    portfolio: List[PortfolioAsset] = Field(..., min_items=1, max_items=10, description="포트폴리오 구성")
    start_date: Union[date, str] = Field(..., description="백테스트 시작 날짜")
    end_date: Union[date, str] = Field(..., description="백테스트 종료 날짜")
    strategy: StrategyType = Field(StrategyType.BUY_AND_HOLD, description="사용할 전략")
    strategy_params: Optional[Dict[str, Any]] = Field(default=None, description="전략 파라미터")
    commission: float = Field(default=0.002, ge=0, le=0.1, description="거래 수수료")
    rebalance_frequency: Optional[str] = Field("monthly", description="리밸런싱 주기")
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            try:
                return datetime.strptime(v, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError('날짜 형식은 YYYY-MM-DD여야 합니다')
        return v
    
    @field_validator('end_date')
    @classmethod
    def end_date_after_start_date(cls, v, info):
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('종료 날짜는 시작 날짜보다 늦어야 합니다')
        return v
