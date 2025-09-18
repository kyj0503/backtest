"""
백테스트 도메인 서비스

백테스트 실행과 관련된 핵심 비즈니스 로직을 담당합니다.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ..entities.backtest_result import BacktestResultEntity
from ..entities.strategy import StrategyEntity
from ..value_objects.date_range import DateRange
from ..value_objects.performance_metrics import PerformanceMetrics


class BacktestDomainService:
    """백테스트 도메인 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_backtest_result(self,
                              strategy: StrategyEntity,
                              symbol: str,
                              date_range: DateRange,
                              backtest_stats,
                              initial_cash: float = 10000.0,
                              commission: float = 0.001,
                              **kwargs) -> BacktestResultEntity:
        """백테스트 결과 엔티티 생성"""
        
        try:
            # 파라미터 유효성 검증
            if initial_cash <= 0:
                raise ValueError("초기 자금은 양수여야 합니다.")
            
            if not (0 <= commission <= 1):
                raise ValueError("수수료는 0-1 범위여야 합니다.")
            
            # 백테스트 결과 엔티티 생성
            result = BacktestResultEntity.from_backtest_stats(
                strategy_name=strategy.name,
                symbol=symbol,
                date_range=date_range,
                stats_series=backtest_stats,
                initial_cash=initial_cash,
                commission=commission,
                strategy_params=kwargs.get('strategy_params', {}),
                **kwargs
            )
            
            # 전략 성과 통계 업데이트
            if result.performance:
                strategy.update_performance_stats(
                    return_pct=result.performance.total_return_pct,
                    sharpe_ratio=result.performance.sharpe_ratio,
                    is_profitable=result.performance.is_profitable()
                )
            
            self.logger.info(f"백테스트 결과 생성 완료: {strategy.name}, {symbol}")
            return result
            
        except Exception as e:
            self.logger.error(f"백테스트 결과 생성 실패: {e}")
            raise
    
    def validate_backtest_request(self,
                                 strategy: StrategyEntity,
                                 symbol: str,
                                 date_range: DateRange,
                                 strategy_params: Dict[str, Any]) -> bool:
        """백테스트 요청 유효성 검증"""
        
        try:
            # 심볼 유효성 검증
            if not symbol or len(symbol) < 1:
                raise ValueError("유효한 심볼을 입력해주세요.")
            
            # 날짜 범위 검증
            if date_range.duration_days() < 30:
                raise ValueError("백테스트 기간은 최소 30일 이상이어야 합니다.")
            
            # 전략 파라미터 검증
            strategy.validate_parameters(strategy_params)
            
            self.logger.info(f"백테스트 요청 검증 완료: {strategy.name}, {symbol}")
            return True
            
        except Exception as e:
            self.logger.error(f"백테스트 요청 검증 실패: {e}")
            raise
    
    def compare_backtest_results(self,
                                result1: BacktestResultEntity,
                                result2: BacktestResultEntity) -> Dict[str, Any]:
        """백테스트 결과 비교"""
        
        if not (result1.performance and result2.performance):
            raise ValueError("성과 지표가 없는 결과는 비교할 수 없습니다.")
        
        comparison = {
            "strategies": {
                "strategy_1": {
                    "name": result1.strategy_name,
                    "symbol": result1.symbol,
                    "period": str(result1.date_range)
                },
                "strategy_2": {
                    "name": result2.strategy_name,
                    "symbol": result2.symbol,
                    "period": str(result2.date_range)
                }
            },
            "performance_comparison": {
                "total_return": {
                    "strategy_1": result1.performance.total_return_pct,
                    "strategy_2": result2.performance.total_return_pct,
                    "difference": result1.performance.total_return_pct - result2.performance.total_return_pct,
                    "winner": "strategy_1" if result1.performance.total_return_pct > result2.performance.total_return_pct else "strategy_2"
                },
                "sharpe_ratio": {
                    "strategy_1": result1.performance.sharpe_ratio,
                    "strategy_2": result2.performance.sharpe_ratio,
                    "difference": result1.performance.sharpe_ratio - result2.performance.sharpe_ratio,
                    "winner": "strategy_1" if result1.performance.sharpe_ratio > result2.performance.sharpe_ratio else "strategy_2"
                },
                "max_drawdown": {
                    "strategy_1": result1.performance.max_drawdown_pct,
                    "strategy_2": result2.performance.max_drawdown_pct,
                    "difference": result1.performance.max_drawdown_pct - result2.performance.max_drawdown_pct,
                    "winner": "strategy_1" if result1.performance.max_drawdown_pct > result2.performance.max_drawdown_pct else "strategy_2"  # 손실이 적은 쪽이 우수
                },
                "volatility": {
                    "strategy_1": result1.performance.volatility_pct,
                    "strategy_2": result2.performance.volatility_pct,
                    "difference": result1.performance.volatility_pct - result2.performance.volatility_pct,
                    "winner": "strategy_1" if result1.performance.volatility_pct < result2.performance.volatility_pct else "strategy_2"  # 변동성이 낮은 쪽이 우수
                }
            },
            "overall_winner": self._determine_overall_winner(result1, result2)
        }
        
        return comparison
    
    def _determine_overall_winner(self,
                                 result1: BacktestResultEntity,
                                 result2: BacktestResultEntity) -> str:
        """종합 우승자 결정"""
        
        # 샤프 비율을 주요 지표로 사용
        if result1.performance.sharpe_ratio > result2.performance.sharpe_ratio:
            return "strategy_1"
        elif result2.performance.sharpe_ratio > result1.performance.sharpe_ratio:
            return "strategy_2"
        else:
            # 샤프 비율이 같으면 총 수익률로 비교
            if result1.performance.total_return_pct > result2.performance.total_return_pct:
                return "strategy_1"
            else:
                return "strategy_2"
    
    def analyze_performance_trends(self,
                                  results: List[BacktestResultEntity]) -> Dict[str, Any]:
        """성과 트렌드 분석"""
        
        if not results:
            return {"error": "분석할 결과가 없습니다."}
        
        # 시간순 정렬
        sorted_results = sorted(results, key=lambda r: r.created_at)
        
        # 트렌드 계산
        returns = [r.performance.total_return_pct for r in sorted_results if r.performance]
        sharpe_ratios = [r.performance.sharpe_ratio for r in sorted_results if r.performance]
        
        if not returns:
            return {"error": "성과 데이터가 없습니다."}
        
        analysis = {
            "summary": {
                "total_backtests": len(results),
                "avg_return": sum(returns) / len(returns),
                "avg_sharpe": sum(sharpe_ratios) / len(sharpe_ratios),
                "best_return": max(returns),
                "worst_return": min(returns),
                "profitable_ratio": len([r for r in returns if r > 0]) / len(returns) * 100
            },
            "trends": {
                "return_trend": self._calculate_trend(returns),
                "sharpe_trend": self._calculate_trend(sharpe_ratios)
            },
            "recent_performance": {
                "last_3": returns[-3:] if len(returns) >= 3 else returns,
                "improvement": returns[-1] > returns[-2] if len(returns) >= 2 else None
            }
        }
        
        return analysis
    
    def _calculate_trend(self, values: List[float]) -> str:
        """트렌드 계산 (간단한 선형 추세)"""
        if len(values) < 2:
            return "insufficient_data"
        
        # 간단한 선형 회귀
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        if slope > 0.1:
            return "improving"
        elif slope < -0.1:
            return "declining"
        else:
            return "stable"
    
    def generate_recommendations(self,
                               result: BacktestResultEntity,
                               strategy: StrategyEntity) -> List[str]:
        """성과 기반 추천사항 생성"""
        
        recommendations = []
        
        if not result.performance:
            return ["성과 데이터가 없어 추천사항을 생성할 수 없습니다."]
        
        perf = result.performance
        
        # 수익률 기반 추천
        if perf.total_return_pct < 0:
            recommendations.append("손실이 발생했습니다. 전략 파라미터를 조정하거나 다른 전략을 고려해보세요.")
        elif perf.total_return_pct < 5:
            recommendations.append("수익률이 낮습니다. 더 공격적인 파라미터나 다른 시장 환경을 시도해보세요.")
        
        # 샤프 비율 기반 추천
        if perf.sharpe_ratio < 0.5:
            recommendations.append("위험 대비 수익이 낮습니다. 리스크 관리 전략을 강화하세요.")
        elif perf.sharpe_ratio > 2.0:
            recommendations.append("우수한 위험 조정 수익률입니다. 이 설정을 다른 종목에도 적용해보세요.")
        
        # 최대 손실 기반 추천
        if perf.max_drawdown_pct < -20:
            recommendations.append("최대 손실이 큽니다. 손절매 로직을 추가하거나 포지션 크기를 줄이세요.")
        
        # 거래 빈도 기반 추천
        if perf.total_trades > 100:
            recommendations.append("거래가 너무 빈번합니다. 거래 비용을 고려하여 필터를 강화하세요.")
        elif perf.total_trades < 5:
            recommendations.append("거래가 너무 적습니다. 전략 조건을 완화하여 더 많은 기회를 포착하세요.")
        
        if not recommendations:
            recommendations.append("양호한 성과입니다. 현재 설정을 유지하면서 다른 종목에도 적용해보세요.")
        
        return recommendations
