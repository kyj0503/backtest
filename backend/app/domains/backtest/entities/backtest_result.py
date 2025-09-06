"""
백테스트 결과 엔티티

백테스트 실행 결과를 나타내는 도메인 엔티티입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from ..value_objects.date_range import DateRange
from ..value_objects.performance_metrics import PerformanceMetrics


@dataclass
class BacktestResultEntity:
    """백테스트 결과 엔티티"""
    
    # 식별자
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    strategy_name: str = ""
    symbol: str = ""
    date_range: Optional[DateRange] = None
    
    # 성과 지표
    performance: Optional[PerformanceMetrics] = None
    
    # 원시 데이터
    raw_stats: Dict[str, Any] = field(default_factory=dict)
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    
    # 설정 정보
    initial_cash: float = 10000.0
    commission: float = 0.001
    strategy_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.strategy_name:
            raise ValueError("전략명은 필수입니다.")
        
        if not self.symbol:
            raise ValueError("심볼은 필수입니다.")
        
        if self.initial_cash <= 0:
            raise ValueError("초기 자금은 양수여야 합니다.")
        
        if not (0 <= self.commission <= 1):
            raise ValueError("수수료는 0-1 범위여야 합니다.")
    
    @classmethod
    def from_backtest_stats(cls, 
                           strategy_name: str,
                           symbol: str,
                           date_range: DateRange,
                           stats_series,
                           trades_df=None,
                           equity_curve_df=None,
                           **kwargs) -> "BacktestResultEntity":
        """백테스트 통계로부터 엔티티 생성"""
        
        # 성과 지표 생성
        performance = PerformanceMetrics.from_backtest_stats(stats_series)
        
        # 원시 통계 데이터 변환
        raw_stats = {}
        for key, value in stats_series.items():
            try:
                # 날짜 타입 처리
                if hasattr(value, 'strftime'):
                    raw_stats[key] = value.strftime('%Y-%m-%d')
                # 숫자 타입 처리
                elif isinstance(value, (int, float)):
                    raw_stats[key] = float(value)
                else:
                    raw_stats[key] = str(value)
            except:
                raw_stats[key] = str(value)
        
        # 거래 내역 변환
        trades = []
        if trades_df is not None and not trades_df.empty:
            trades = trades_df.to_dict('records')
        
        # 자산 곡선 변환
        equity_curve = []
        if equity_curve_df is not None and not equity_curve_df.empty:
            equity_curve = equity_curve_df.to_dict('records')
        
        return cls(
            strategy_name=strategy_name,
            symbol=symbol,
            date_range=date_range,
            performance=performance,
            raw_stats=raw_stats,
            trades=trades,
            equity_curve=equity_curve,
            **kwargs
        )
    
    def update_performance(self, new_performance: PerformanceMetrics):
        """성과 지표 업데이트"""
        self.performance = new_performance
        self.updated_at = datetime.now()
    
    def add_trade(self, trade_data: Dict[str, Any]):
        """거래 내역 추가"""
        self.trades.append(trade_data)
        self.updated_at = datetime.now()
    
    def get_duration_days(self) -> int:
        """백테스트 기간 (일수)"""
        return self.date_range.duration_days() if self.date_range else 0
    
    def get_total_trades(self) -> int:
        """총 거래 수"""
        return len(self.trades)
    
    def get_final_value(self) -> float:
        """최종 포트폴리오 가치"""
        if not self.equity_curve:
            return self.initial_cash
        return self.equity_curve[-1].get('equity', self.initial_cash)
    
    def get_profit_loss(self) -> float:
        """손익금액"""
        return self.get_final_value() - self.initial_cash
    
    def is_profitable(self) -> bool:
        """수익성 여부"""
        return self.performance.is_profitable() if self.performance else False
    
    def get_risk_level(self) -> str:
        """위험 수준"""
        return self.performance.risk_grade() if self.performance else "알 수 없음"
    
    def to_summary(self) -> Dict[str, Any]:
        """요약 정보"""
        summary = {
            "id": self.id,
            "strategy_name": self.strategy_name,
            "symbol": self.symbol,
            "period": str(self.date_range) if self.date_range else "알 수 없음",
            "initial_cash": self.initial_cash,
            "final_value": self.get_final_value(),
            "profit_loss": self.get_profit_loss(),
            "total_trades": self.get_total_trades(),
            "created_at": self.created_at.isoformat()
        }
        
        if self.performance:
            summary.update(self.performance.to_summary_dict())
        
        return summary
    
    def to_detailed_dict(self) -> Dict[str, Any]:
        """상세 정보"""
        return {
            "metadata": {
                "id": self.id,
                "strategy_name": self.strategy_name,
                "symbol": self.symbol,
                "date_range": self.date_range.to_dict() if self.date_range else None,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
                "user_id": self.user_id
            },
            "configuration": {
                "initial_cash": self.initial_cash,
                "commission": self.commission,
                "strategy_params": self.strategy_params
            },
            "performance": self.performance.to_detailed_dict() if self.performance else None,
            "statistics": {
                "total_trades": self.get_total_trades(),
                "final_value": self.get_final_value(),
                "profit_loss": self.get_profit_loss(),
                "duration_days": self.get_duration_days()
            },
            "raw_stats": self.raw_stats
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (f"BacktestResult({self.strategy_name}, {self.symbol}, "
                f"{self.date_range}, 수익률: {self.performance.total_return_pct if self.performance else 'N/A'}%)")
