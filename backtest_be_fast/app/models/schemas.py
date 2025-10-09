"""
포트폴리오 백테스트 관련 스키마
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import numpy as np

from ..core.config import settings


class PortfolioStock(BaseModel):
    """포트폴리오 종목 모델"""
    symbol: str = Field(..., min_length=1, max_length=settings.max_symbol_length, description="주식 심볼")
    amount: Optional[float] = Field(None, gt=0, description="투자 금액 (> 0, weight와 동시 입력 불가)")
    weight: Optional[float] = Field(None, ge=0, le=100, description="비중(%) (0~100, amount와 동시 입력 불가, 소수점 허용)")
    investment_type: Optional[str] = Field("lump_sum", description="투자 방식 (lump_sum, dca)")
    dca_periods: Optional[int] = Field(settings.default_dca_periods, ge=1, le=settings.max_dca_periods, description="분할 매수 기간 (개월)")
    asset_type: Optional[str] = Field("stock", description="자산 타입 (stock, cash)")
    custom_name: Optional[str] = Field(None, description="현금 자산의 커스텀 이름")
    @field_validator('amount', 'weight')
    @classmethod
    def validate_amount_weight_exclusive(cls, v, info):
        # amount와 weight는 동시에 입력 불가
        data = info.data
        amount = data.get('amount')
        weight = data.get('weight')
        if amount is not None and weight is not None:
            raise ValueError('amount와 weight는 동시에 입력할 수 없습니다. 하나만 입력하세요.')
        return v
    
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
    portfolio: List[PortfolioStock] = Field(..., min_length=1, max_length=settings.max_portfolio_items, description="포트폴리오 구성")
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
        
        # amount/weight 혼합 입력 불가, 모두 amount만 입력 or 모두 weight만 입력 or 일부만 weight면 amount 자동 환산
        has_amount = any(item.amount is not None for item in v)
        has_weight = any(item.weight is not None for item in v)
        if has_amount and has_weight:
            raise ValueError('포트폴리오 내 모든 종목은 amount 또는 weight 중 하나만 입력해야 합니다. 혼합 입력 불가.')
        
        if has_weight:
            total_weight = sum(item.weight or 0 for item in v)
            # 0~100 허용, 100±0.01 이내만 통과
            if not (99.99 <= total_weight <= 100.01):
                raise ValueError(f'종목 비중(weight) 합계가 100이 아닙니다. 현재 합계: {total_weight}')
        else:
            total_amount = sum(item.amount or 0 for item in v)
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
            if (end - start).days > 365 * settings.max_backtest_duration_years:
                raise ValueError(f'백테스트 기간은 최대 {settings.max_backtest_duration_years}년으로 제한됩니다.')
        return v

 
