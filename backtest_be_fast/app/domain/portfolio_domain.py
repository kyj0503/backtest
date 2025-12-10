from datetime import date
from typing import Dict, List, Optional, Any, Set
from pydantic import BaseModel, Field


class DcaStrategyInfo(BaseModel):
    """
    DCA 전략 및 투자 정보 모델
    
    기존의 dca_info 딕셔너리를 대체합니다.
    """
    symbol: str = Field(..., description="종목 심볼")
    allocation: float = Field(..., description="목표 비중 (0.0 ~ 1.0)")
    asset_type: str = Field(..., description="자산 유형 ('stock', 'cash' 등)")
    investment_type: str = Field(..., description="투자 방식 ('lump_sum', 'dca')")
    monthly_amount: float = Field(..., description="월별 투자 금액 (DCA) 또는 총 투자 금액 (Lump sum)")
    dca_frequency: str = Field(default="monthly", description="DCA 주기")
    dca_periods: int = Field(default=0, description="DCA 총 횟수")
    
    # 실행 상태 관리
    executed_count: int = Field(default=0, description="현재까지 실행된 DCA 횟수")
    last_dca_date: Optional[date] = Field(default=None, description="마지막 DCA 실행 날짜")
    original_nth_weekday: Optional[int] = Field(default=None, description="최초 DCA 실행 시의 n번째 요일 정보")

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True
    }

class PortfolioState(BaseModel):
    """
    포트폴리오 시뮬레이션 상태 모델
    
    기존의 state 딕셔너리를 대체합니다.
    """
    shares: Dict[str, float] = Field(default_factory=dict, description="종목별 보유 주식 수")
    portfolio_values: List[Dict[str, Any]] = Field(default_factory=list, description="일별 포트폴리오 가치 기록")
    daily_returns: List[float] = Field(default_factory=list, description="일별 수익률")
    
    prev_portfolio_value: float = Field(default=0.0, description="전일 포트폴리오 총 가치")
    prev_date: Optional[date] = Field(default=None, description="전일 날짜")
    is_first_day: bool = Field(default=True, description="첫 날 여부")
    
    available_cash: float = Field(default=0.0, description="가용 현금")
    cash_holdings: Dict[str, float] = Field(default_factory=dict, description="종목별 현금 보유량 (초기 할당분)")
    
    total_trades: int = Field(default=0, description="총 거래 횟수")
    rebalance_history: List[Dict[str, Any]] = Field(default_factory=list, description="리밸런싱 기록")
    weight_history: List[Dict[str, Any]] = Field(default_factory=list, description="비중 변화 기록")
    
    last_rebalance_date: Optional[date] = Field(default=None, description="마지막 리밸런싱 날짜")
    original_rebalance_nth: Optional[int] = Field(default=None, description="리밸런싱 기준 n번째 요일")
    
    last_valid_prices: Dict[str, float] = Field(default_factory=dict, description="종목별 마지막 유효 가격")
    last_price_date: Dict[str, date] = Field(default_factory=dict, description="종목별 마지막 가격 날짜")
    delisted_stocks: Set[str] = Field(default_factory=set, description="상장폐지된 종목 집합")

    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True
    }
