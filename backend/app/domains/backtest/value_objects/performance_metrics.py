"""
성과 지표 값 객체 (Value Object)

백테스트 성과를 나타내는 불변 객체입니다.
"""
from dataclasses import dataclass
from typing import Optional
import math


@dataclass(frozen=True)
class PerformanceMetrics:
    """백테스트 성과 지표 값 객체"""
    
    # 수익률 관련
    total_return_pct: float
    annual_return_pct: float
    volatility_pct: float
    
    # 위험 지표
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    
    # 거래 관련
    total_trades: int
    win_rate_pct: float
    
    # 벤치마크 대비
    benchmark_return_pct: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    
    def __post_init__(self):
        """초기화 후 검증"""
        # 기본 검증
        if self.volatility_pct < 0:
            raise ValueError("변동성은 음수일 수 없습니다.")
        
        if self.max_drawdown_pct > 0:
            raise ValueError("최대 손실률은 0 이하여야 합니다.")
        
        if not (0 <= self.win_rate_pct <= 100):
            raise ValueError("승률은 0-100% 범위여야 합니다.")
        
        if self.total_trades < 0:
            raise ValueError("총 거래수는 음수일 수 없습니다.")
    
    @classmethod
    def from_backtest_stats(cls, stats_series) -> "PerformanceMetrics":
        """backtesting 라이브러리 결과로부터 생성"""
        try:
            # backtesting 라이브러리 결과 파싱
            total_return = float(stats_series.get('Return [%]', 0))
            annual_return = float(stats_series.get('Return (Ann.) [%]', 0))
            volatility = float(stats_series.get('Volatility (Ann.) [%]', 0))
            sharpe = float(stats_series.get('Sharpe Ratio', 0))
            sortino = float(stats_series.get('Sortino Ratio', 0))
            max_dd = float(stats_series.get('Max. Drawdown [%]', 0))
            
            # 거래 관련 통계 (안전하게 처리)
            total_trades = int(stats_series.get('# Trades', 0))
            win_rate = float(stats_series.get('Win Rate [%]', 0))
            
            # 벤치마크 관련 (선택사항)
            benchmark_return = stats_series.get('Buy & Hold Return [%]')
            if benchmark_return is not None:
                benchmark_return = float(benchmark_return)
            
            return cls(
                total_return_pct=total_return,
                annual_return_pct=annual_return,
                volatility_pct=volatility,
                sharpe_ratio=sharpe,
                sortino_ratio=sortino,
                max_drawdown_pct=max_dd,
                total_trades=total_trades,
                win_rate_pct=win_rate,
                benchmark_return_pct=benchmark_return
            )
        except (ValueError, KeyError, TypeError) as e:
            raise ValueError(f"백테스트 통계 파싱 오류: {e}")
    
    def risk_adjusted_return(self) -> float:
        """위험 조정 수익률 (Sharpe Ratio 기반)"""
        return self.sharpe_ratio
    
    def excess_return_vs_benchmark(self) -> Optional[float]:
        """벤치마크 대비 초과 수익률"""
        if self.benchmark_return_pct is None:
            return None
        return self.total_return_pct - self.benchmark_return_pct
    
    def is_profitable(self) -> bool:
        """수익성 여부"""
        return self.total_return_pct > 0
    
    def is_outperforming_benchmark(self) -> Optional[bool]:
        """벤치마크 대비 우수 성과 여부"""
        excess = self.excess_return_vs_benchmark()
        return excess > 0 if excess is not None else None
    
    def risk_grade(self) -> str:
        """위험 등급 평가"""
        if self.volatility_pct <= 5:
            return "매우 낮음"
        elif self.volatility_pct <= 10:
            return "낮음"
        elif self.volatility_pct <= 15:
            return "보통"
        elif self.volatility_pct <= 25:
            return "높음"
        else:
            return "매우 높음"
    
    def performance_grade(self) -> str:
        """성과 등급 평가"""
        if self.sharpe_ratio >= 2.0:
            return "우수"
        elif self.sharpe_ratio >= 1.0:
            return "양호"
        elif self.sharpe_ratio >= 0.5:
            return "보통"
        elif self.sharpe_ratio >= 0:
            return "미흡"
        else:
            return "불량"
    
    def to_summary_dict(self) -> dict:
        """요약 정보 딕셔너리"""
        summary = {
            "total_return": f"{self.total_return_pct:.2f}%",
            "annual_return": f"{self.annual_return_pct:.2f}%",
            "volatility": f"{self.volatility_pct:.2f}%",
            "sharpe_ratio": round(self.sharpe_ratio, 3),
            "max_drawdown": f"{self.max_drawdown_pct:.2f}%",
            "risk_grade": self.risk_grade(),
            "performance_grade": self.performance_grade(),
            "is_profitable": self.is_profitable()
        }
        
        # 벤치마크 관련 정보 추가
        if self.benchmark_return_pct is not None:
            summary["benchmark_return"] = f"{self.benchmark_return_pct:.2f}%"
            excess = self.excess_return_vs_benchmark()
            summary["excess_return"] = f"{excess:.2f}%" if excess else "N/A"
            summary["outperforming"] = self.is_outperforming_benchmark()
        
        return summary
    
    def to_detailed_dict(self) -> dict:
        """상세 정보 딕셔너리"""
        return {
            "returns": {
                "total_return_pct": self.total_return_pct,
                "annual_return_pct": self.annual_return_pct,
                "benchmark_return_pct": self.benchmark_return_pct
            },
            "risk_metrics": {
                "volatility_pct": self.volatility_pct,
                "sharpe_ratio": self.sharpe_ratio,
                "sortino_ratio": self.sortino_ratio,
                "max_drawdown_pct": self.max_drawdown_pct
            },
            "trading_stats": {
                "total_trades": self.total_trades,
                "win_rate_pct": self.win_rate_pct
            },
            "grades": {
                "risk_grade": self.risk_grade(),
                "performance_grade": self.performance_grade()
            }
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (f"수익률: {self.total_return_pct:.2f}%, "
                f"샤프비율: {self.sharpe_ratio:.2f}, "
                f"최대손실: {self.max_drawdown_pct:.2f}%")
