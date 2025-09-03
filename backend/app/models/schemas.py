from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np
import json

class JSONEncoder(json.JSONEncoder):
    """무한대와 NaN 값을 처리하는 JSON 인코더"""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isinf(obj):
                return 0.0 if obj < 0 else 1e9
            if np.isnan(obj):
                return 0.0
        return super().default(obj)

class StrategyParams(BaseModel):
    """전략 파라미터 모델"""
    sma_short: int = Field(10, ge=2, le=200, description="단기 이동평균 기간")
    sma_long: int = Field(20, ge=5, le=500, description="장기 이동평균 기간")
    position_size: float = Field(0.5, ge=0.1, le=1.0, description="포지션 크기 (0.1 ~ 1.0)")

    @field_validator('sma_long')
    @classmethod
    def validate_sma_long(cls, v, info):
        if 'sma_short' in info.data and v <= info.data['sma_short']:
            raise ValueError('장기 이동평균 기간은 단기 이동평균 기간보다 커야 합니다.')
        return v

    @field_validator('*', mode='before')
    @classmethod
    def validate_float(cls, v):
        if isinstance(v, float):
            if np.isinf(v):
                return 0.0 if v < 0 else 1e9
            if np.isnan(v):
                return 0.0
        return v

class PortfolioStock(BaseModel):
    """포트폴리오 종목 모델"""
    symbol: str = Field(..., min_length=1, max_length=10, description="주식 심볼")
    amount: float = Field(..., gt=0, description="투자 금액 (> 0)")
    investment_type: Optional[str] = Field("lump_sum", description="투자 방식 (lump_sum, dca)")
    dca_periods: Optional[int] = Field(12, ge=1, le=60, description="분할 매수 기간 (개월)")
    asset_type: Optional[str] = Field("stock", description="자산 타입 (stock, cash)")
    
    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v, info):
        # asset_type이 'cash'인 경우 더 유연한 검증
        asset_type = info.data.get('asset_type', 'stock')
        if asset_type == 'cash':
            # 현금 자산은 심볼 제한 없음 (한글 "현금" 등 허용)
            return v
        
        # CASH는 특별한 심볼로 허용
        if v.upper() == 'CASH':
            return v.upper()
        if not v.isalpha():
            raise ValueError('주식 심볼은 영문자만 포함해야 합니다.')
        return v.upper()
    
    @field_validator('investment_type')
    @classmethod
    def validate_investment_type(cls, v):
        if v not in ['lump_sum', 'dca']:
            raise ValueError('투자 방식은 lump_sum 또는 dca만 가능합니다.')
        return v
    
    @field_validator('asset_type')
    @classmethod
    def validate_asset_type(cls, v):
        if v not in ['stock', 'cash']:
            raise ValueError('자산 타입은 stock 또는 cash만 가능합니다.')
        return v

class PortfolioBacktestRequest(BaseModel):
    """포트폴리오 백테스트 요청 모델"""
    portfolio: List[PortfolioStock] = Field(..., min_length=1, max_length=10, description="포트폴리오 구성")
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")
    commission: float = Field(0.002, ge=0, lt=0.1, description="수수료율 (0 ~ 0.1)")
    rebalance_frequency: str = Field("monthly", description="리밸런싱 주기 (monthly, quarterly, yearly)")
    strategy: str = Field("buy_and_hold", description="전략명")
    strategy_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="전략 파라미터")
    
    @field_validator('portfolio')
    @classmethod
    def validate_portfolio(cls, v):
        if not v:
            raise ValueError('포트폴리오는 최소 1개 종목을 포함해야 합니다.')
        
        # 총 투자 금액 확인
        total_amount = sum(item.amount for item in v)
        if total_amount <= 0:
            raise ValueError('총 투자 금액은 0보다 커야 합니다.')
        
        return v
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다.')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data:
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('종료 날짜는 시작 날짜보다 이후여야 합니다.')
            if (end - start).days > 365 * 5:  # 5년 제한
                raise ValueError('백테스트 기간은 최대 5년으로 제한됩니다.')
        return v

class BacktestRequest(BaseModel):
    """백테스트 요청 모델"""
    symbol: str = Field(..., min_length=1, max_length=10, description="주식 심볼")
    start_date: str = Field(..., description="시작 날짜 (YYYY-MM-DD)")
    end_date: str = Field(..., description="종료 날짜 (YYYY-MM-DD)")
    cash: float = Field(10000, gt=0, description="초기 자본금")
    commission: float = Field(0.002, ge=0, lt=0.1, description="수수료율 (0 ~ 0.1)")
    strategy: StrategyParams = Field(default_factory=StrategyParams, description="전략 파라미터")

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v):
        if not v.isalpha():
            raise ValueError('주식 심볼은 영문자만 포함해야 합니다.')
        return v.upper()

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다.')
        return v

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data:
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError('종료 날짜는 시작 날짜보다 이후여야 합니다.')
            if (end - start).days > 365 * 5:  # 5년 제한
                raise ValueError('백테스트 기간은 최대 5년으로 제한됩니다.')
        return v

class Trade(BaseModel):
    """거래 정보 모델"""
    Size: float
    EntryBar: int
    ExitBar: int
    EntryPrice: float
    ExitPrice: float
    PnL: float
    ReturnPct: float
    EntryTime: str
    ExitTime: str
    Duration: str

class TradeSummary(BaseModel):
    """거래 요약 정보 모델"""
    trades: List[Trade]
    total_trades: int
    win_rate: float
    profit_factor: float
    expectancy: float

class EquityData(BaseModel):
    """자본금 데이터 모델"""
    equity_curve: Dict[str, float]
    drawdown: Dict[str, float]

class BacktestData(BaseModel):
    """백테스트 결과 데이터 모델"""
    Start: str
    End: str
    Duration: str
    Exposure_Time: float = Field(..., alias="Exposure Time [%]")
    Equity_Final: float = Field(..., alias="Equity Final [$]")
    Equity_Peak: float = Field(..., alias="Equity Peak [$]")
    Return: float = Field(..., alias="Return [%]")
    Buy_Hold_Return: float = Field(..., alias="Buy & Hold Return [%]")
    Max_Drawdown: float = Field(..., alias="Max. Drawdown [%]")
    Avg_Drawdown: float = Field(..., alias="Avg. Drawdown [%]")
    Max_Drawdown_Duration: str = Field(..., alias="Max. Drawdown Duration")
    Avg_Drawdown_Duration: str = Field(..., alias="Avg. Drawdown Duration")
    Total_Trades: int = Field(..., alias="# Trades")
    Win_Rate: float = Field(..., alias="Win Rate [%]")
    Best_Trade: float = Field(..., alias="Best Trade [%]")
    Worst_Trade: float = Field(..., alias="Worst Trade [%]")
    Avg_Trade: float = Field(..., alias="Avg. Trade [%]")
    Max_Trade_Duration: str = Field(..., alias="Max. Trade Duration")
    Avg_Trade_Duration: str = Field(..., alias="Avg. Trade Duration")
    Profit_Factor: float = Field(..., alias="Profit Factor")
    Expectancy: float = Field(..., alias="Expectancy [%]")
    trades: TradeSummary
    equity: Optional[EquityData] = None

    @field_validator('*', mode='before')
    @classmethod
    def replace_nan(cls, v):
        if isinstance(v, float) and np.isnan(v):
            return 0.0
        return v

class BacktestResponse(BaseModel):
    """백테스트 응답 모델"""
    status: str
    data: BacktestData
    warnings: Optional[List[str]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d"),
            np.float64: lambda v: float(v) if not np.isnan(v) else 0.0,
            np.int64: lambda v: int(v)
        }

class BacktestError(BaseModel):
    """백테스트 오류 응답 모델"""
    error: str
    code: str

class StockPrice(BaseModel):
    """주가 데이터 모델"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int

class StockPriceResponse(BaseModel):
    """주가 응답 모델"""
    symbol: str
    last_updated: datetime
    prices: List[StockPrice]

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

class StockPriceError(BaseModel):
    """주가 오류 응답 모델"""
    error: str
    code: str

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        } 