"""
전략 도메인 서비스

투자 전략 관리와 관련된 핵심 비즈니스 로직을 담당합니다.
"""
from typing import Dict, Any, List, Type, Optional
import logging
import importlib
from datetime import datetime

from ..entities.strategy import StrategyEntity


class StrategyDomainService:
    """전략 도메인 서비스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._strategy_registry: Dict[str, StrategyEntity] = {}
    
    def register_strategy(self,
                         name: str,
                         strategy_class: Type,
                         display_name: str = None,
                         description: str = None,
                         category: str = "기술적분석",
                         parameters: Dict[str, Dict[str, Any]] = None,
                         constraints: List[str] = None) -> StrategyEntity:
        """전략 등록"""
        
        try:
            # 전략 엔티티 생성
            strategy = StrategyEntity.from_strategy_class(
                name=name,
                strategy_class=strategy_class,
                display_name=display_name or name,
                description=description,
                category=category,
                constraints=constraints or []
            )
            
            # 파라미터 등록
            if parameters:
                for param_name, param_info in parameters.items():
                    strategy.add_parameter(
                        param_name=param_name,
                        param_type=param_info.get('type', str),
                        default_value=param_info.get('default'),
                        min_value=param_info.get('min'),
                        max_value=param_info.get('max'),
                        description=param_info.get('description', '')
                    )
            
            # 레지스트리에 등록
            self._strategy_registry[name] = strategy
            
            self.logger.info(f"전략 등록 완료: {name}")
            return strategy
            
        except Exception as e:
            self.logger.error(f"전략 등록 실패 {name}: {e}")
            raise
    
    def get_strategy(self, name: str) -> Optional[StrategyEntity]:
        """전략 조회"""
        return self._strategy_registry.get(name)
    
    def get_all_strategies(self) -> Dict[str, StrategyEntity]:
        """모든 전략 조회"""
        return self._strategy_registry.copy()
    
    def get_strategies_by_category(self, category: str) -> Dict[str, StrategyEntity]:
        """카테고리별 전략 조회"""
        return {
            name: strategy 
            for name, strategy in self._strategy_registry.items()
            if strategy.category == category
        }
    
    def create_strategy_instance(self,
                                name: str,
                                parameters: Dict[str, Any] = None) -> Any:
        """전략 인스턴스 생성"""
        
        strategy = self.get_strategy(name)
        if not strategy:
            raise ValueError(f"전략을 찾을 수 없습니다: {name}")
        
        if not strategy.strategy_class:
            raise ValueError(f"전략 클래스가 설정되지 않았습니다: {name}")
        
        try:
            # 파라미터 병합 및 검증
            final_params = strategy.get_merged_parameters(parameters)
            strategy.validate_parameters(final_params)
            
            # 전략 인스턴스 생성
            strategy_instance = strategy.strategy_class()
            
            # 파라미터 설정
            for param_name, param_value in final_params.items():
                if hasattr(strategy_instance, param_name):
                    setattr(strategy_instance, param_name, param_value)
            
            self.logger.info(f"전략 인스턴스 생성 완료: {name}")
            return strategy_instance
            
        except Exception as e:
            self.logger.error(f"전략 인스턴스 생성 실패 {name}: {e}")
            raise
    
    def validate_strategy_parameters(self,
                                   name: str,
                                   parameters: Dict[str, Any]) -> bool:
        """전략 파라미터 유효성 검증"""
        
        strategy = self.get_strategy(name)
        if not strategy:
            raise ValueError(f"전략을 찾을 수 없습니다: {name}")
        
        return strategy.validate_parameters(parameters)
    
    def get_strategy_metadata(self, name: str) -> Dict[str, Any]:
        """전략 메타데이터 조회"""
        
        strategy = self.get_strategy(name)
        if not strategy:
            raise ValueError(f"전략을 찾을 수 없습니다: {name}")
        
        return strategy.to_metadata_dict()
    
    def update_strategy_performance(self,
                                   name: str,
                                   return_pct: float,
                                   sharpe_ratio: float,
                                   is_profitable: bool):
        """전략 성과 통계 업데이트"""
        
        strategy = self.get_strategy(name)
        if strategy:
            strategy.update_performance_stats(return_pct, sharpe_ratio, is_profitable)
            self.logger.info(f"전략 성과 업데이트: {name}")
    
    def get_top_performing_strategies(self, limit: int = 5) -> List[StrategyEntity]:
        """성과 상위 전략 조회"""
        
        strategies = list(self._strategy_registry.values())
        
        # 평균 샤프 비율 기준 정렬
        strategies.sort(key=lambda s: s.avg_sharpe_ratio, reverse=True)
        
        return strategies[:limit]
    
    def get_strategy_performance_summary(self) -> Dict[str, Any]:
        """전략 성과 요약"""
        
        strategies = list(self._strategy_registry.values())
        
        if not strategies:
            return {"total_strategies": 0}
        
        total_backtests = sum(s.total_backtests for s in strategies)
        avg_return = sum(s.avg_return for s in strategies) / len(strategies)
        avg_sharpe = sum(s.avg_sharpe_ratio for s in strategies) / len(strategies)
        avg_success_rate = sum(s.success_rate for s in strategies) / len(strategies)
        
        return {
            "total_strategies": len(strategies),
            "total_backtests": total_backtests,
            "average_return": round(avg_return, 2),
            "average_sharpe_ratio": round(avg_sharpe, 3),
            "average_success_rate": round(avg_success_rate, 1),
            "top_performers": [s.to_summary_dict() for s in self.get_top_performing_strategies(3)]
        }
    
    def recommend_strategies_for_symbol(self,
                                       symbol: str,
                                       risk_tolerance: str = "medium") -> List[StrategyEntity]:
        """종목별 추천 전략"""
        
        # 간단한 추천 로직 (향후 더 정교하게 발전 가능)
        all_strategies = list(self._strategy_registry.values())
        
        # 성과 기준 필터링
        recommended = []
        
        for strategy in all_strategies:
            # 최소 백테스트 수행 횟수
            if strategy.total_backtests < 1:
                continue
            
            # 리스크 허용도에 따른 필터링
            if risk_tolerance == "low":
                if strategy.avg_sharpe_ratio >= 1.0 and strategy.success_rate >= 70:
                    recommended.append(strategy)
            elif risk_tolerance == "medium":
                if strategy.avg_sharpe_ratio >= 0.5 and strategy.success_rate >= 50:
                    recommended.append(strategy)
            else:  # high
                if strategy.avg_return >= 10 or strategy.avg_sharpe_ratio >= 0.3:
                    recommended.append(strategy)
        
        # 성과 순으로 정렬
        recommended.sort(key=lambda s: s.avg_sharpe_ratio, reverse=True)
        
        return recommended[:5]  # 상위 5개만 반환
    
    def analyze_strategy_correlation(self,
                                   strategies: List[str]) -> Dict[str, Any]:
        """전략 간 상관관계 분석 (기본 구현)"""
        
        analysis = {
            "strategies": strategies,
            "total_combinations": len(strategies) * (len(strategies) - 1) // 2,
            "recommendations": []
        }
        
        # 카테고리별 그룹화
        category_groups = {}
        for strategy_name in strategies:
            strategy = self.get_strategy(strategy_name)
            if strategy:
                category = strategy.category
                if category not in category_groups:
                    category_groups[category] = []
                category_groups[category].append(strategy_name)
        
        # 다양성 분석
        if len(category_groups) > 1:
            analysis["recommendations"].append("다양한 카테고리의 전략으로 분산 효과를 기대할 수 있습니다.")
        else:
            analysis["recommendations"].append("동일 카테고리 전략들입니다. 다른 카테고리 전략 추가를 고려하세요.")
        
        analysis["category_distribution"] = category_groups
        
        return analysis
    
    def export_strategy_definitions(self) -> Dict[str, Any]:
        """전략 정의 내보내기"""
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_strategies": len(self._strategy_registry),
            "strategies": {}
        }
        
        for name, strategy in self._strategy_registry.items():
            export_data["strategies"][name] = {
                "metadata": strategy.to_metadata_dict(),
                "module_path": strategy.module_path,
                "class_name": strategy.strategy_class.__name__ if strategy.strategy_class else None
            }
        
        return export_data
    
    def clear_registry(self):
        """레지스트리 초기화 (테스트용)"""
        self._strategy_registry.clear()
        self.logger.info("전략 레지스트리가 초기화되었습니다.")
