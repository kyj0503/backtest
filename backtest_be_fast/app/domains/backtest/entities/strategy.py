"""
전략 엔티티

투자 전략을 나타내는 도메인 엔티티입니다.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Type
import uuid


@dataclass
class StrategyEntity:
    """전략 엔티티"""
    
    # 식별자
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # 기본 정보
    name: str = ""
    display_name: str = ""
    description: str = ""
    category: str = "기술적분석"
    
    # 전략 클래스 정보
    strategy_class: Optional[Type] = None
    module_path: str = ""
    
    # 파라미터 정의
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_params: Dict[str, Any] = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    
    # 메타데이터
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    author: str = ""
    
    # 성과 통계 (누적)
    total_backtests: int = 0
    avg_return: float = 0.0
    avg_sharpe_ratio: float = 0.0
    success_rate: float = 0.0  # 수익을 낸 백테스트 비율
    
    def __post_init__(self):
        """초기화 후 검증"""
        if not self.name:
            raise ValueError("전략명은 필수입니다.")
        
        if not self.display_name:
            self.display_name = self.name
        
        if not self.description:
            self.description = f"{self.display_name} 전략"
    
    @classmethod
    def from_strategy_class(cls, 
                           name: str,
                           strategy_class: Type,
                           **kwargs) -> "StrategyEntity":
        """전략 클래스로부터 엔티티 생성"""
        
        # 클래스 docstring에서 정보 추출
        description = getattr(strategy_class, '__doc__', '') or f"{name} 전략"
        module_path = f"{strategy_class.__module__}.{strategy_class.__name__}"
        
        return cls(
            name=name,
            strategy_class=strategy_class,
            description=description.strip(),
            module_path=module_path,
            **kwargs
        )
    
    def add_parameter(self, 
                     param_name: str,
                     param_type: Type,
                     default_value: Any,
                     min_value: Any = None,
                     max_value: Any = None,
                     description: str = ""):
        """파라미터 추가"""
        
        param_info = {
            'type': param_type,
            'default': default_value,
            'description': description
        }
        
        if min_value is not None:
            param_info['min'] = min_value
        
        if max_value is not None:
            param_info['max'] = max_value
        
        self.parameters[param_name] = param_info
        self.default_params[param_name] = default_value
        self.updated_at = datetime.now()
    
    def validate_parameters(self, params: Dict[str, Any]) -> bool:
        """파라미터 유효성 검증"""
        for param_name, param_value in params.items():
            if param_name not in self.parameters:
                raise ValueError(f"알 수 없는 파라미터: {param_name}")
            
            param_info = self.parameters[param_name]
            
            # 타입 검증
            expected_type = param_info['type']
            if not isinstance(param_value, expected_type):
                try:
                    # 타입 변환 시도
                    param_value = expected_type(param_value)
                    params[param_name] = param_value
                except (ValueError, TypeError):
                    raise ValueError(f"파라미터 {param_name}의 타입이 올바르지 않습니다. "
                                   f"기대: {expected_type.__name__}, 실제: {type(param_value).__name__}")
            
            # 범위 검증
            if 'min' in param_info and param_value < param_info['min']:
                raise ValueError(f"파라미터 {param_name}이 최소값({param_info['min']})보다 작습니다.")
            
            if 'max' in param_info and param_value > param_info['max']:
                raise ValueError(f"파라미터 {param_name}이 최대값({param_info['max']})보다 큽니다.")
        
        # 제약조건 검증
        for constraint in self.constraints:
            if not self._evaluate_constraint(constraint, params):
                raise ValueError(f"제약조건 위반: {constraint}")
        
        return True
    
    def _evaluate_constraint(self, constraint: str, params: Dict[str, Any]) -> bool:
        """제약조건 평가"""
        try:
            # 안전한 constraint 평가 (간단한 경우만)
            if '<' in constraint:
                left, right = constraint.split('<')
                left_val = params.get(left.strip(), 0)
                right_val = params.get(right.strip(), 0)
                return left_val < right_val
            elif '>' in constraint:
                left, right = constraint.split('>')
                left_val = params.get(left.strip(), 0)
                right_val = params.get(right.strip(), 0)
                return left_val > right_val
            else:
                return True  # 복잡한 제약조건은 일단 통과
        except:
            return True  # 평가 오류시 일단 통과
    
    def get_merged_parameters(self, user_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """기본값과 사용자 파라미터를 병합"""
        merged = self.default_params.copy()
        if user_params:
            merged.update(user_params)
        return merged
    
    def update_performance_stats(self, 
                                return_pct: float,
                                sharpe_ratio: float,
                                is_profitable: bool):
        """성과 통계 업데이트"""
        # 누적 평균 계산
        total = self.total_backtests
        self.avg_return = (self.avg_return * total + return_pct) / (total + 1)
        self.avg_sharpe_ratio = (self.avg_sharpe_ratio * total + sharpe_ratio) / (total + 1)
        
        # 성공률 업데이트
        successful_backtests = int(self.success_rate * total / 100)
        if is_profitable:
            successful_backtests += 1
        self.success_rate = (successful_backtests / (total + 1)) * 100
        
        self.total_backtests += 1
        self.updated_at = datetime.now()
    
    def get_parameter_info(self, param_name: str) -> Optional[Dict[str, Any]]:
        """특정 파라미터 정보 조회"""
        return self.parameters.get(param_name)
    
    def is_parameter_required(self, param_name: str) -> bool:
        """필수 파라미터 여부"""
        return param_name in self.parameters
    
    def to_metadata_dict(self) -> Dict[str, Any]:
        """메타데이터 딕셔너리"""
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "author": self.author,
            "parameters": self.parameters,
            "default_params": self.default_params,
            "constraints": self.constraints,
            "performance_stats": {
                "total_backtests": self.total_backtests,
                "avg_return": round(self.avg_return, 2),
                "avg_sharpe_ratio": round(self.avg_sharpe_ratio, 3),
                "success_rate": round(self.success_rate, 1)
            }
        }
    
    def to_summary_dict(self) -> Dict[str, Any]:
        """요약 정보 딕셔너리"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "param_count": len(self.parameters),
            "total_backtests": self.total_backtests,
            "avg_return": f"{self.avg_return:.2f}%",
            "success_rate": f"{self.success_rate:.1f}%"
        }
    
    def __str__(self) -> str:
        """문자열 표현"""
        return (f"Strategy({self.name}, {self.category}, "
                f"평균수익률: {self.avg_return:.2f}%, "
                f"성공률: {self.success_rate:.1f}%)")
