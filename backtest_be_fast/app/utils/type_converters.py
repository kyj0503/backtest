"""
타입 변환 유틸리티

**역할**:
- 안전한 타입 변환 함수 제공 (NaN, None 처리)
- 코드 중복 제거 (backtest_engine, chart_data_service)

**주요 기능**:
1. safe_float(): 안전한 float 변환
2. safe_int(): 안전한 int 변환
3. safe_str(): 안전한 str 변환

**사용 예**:
```python
from app.utils.type_converters import safe_float, safe_int

value = safe_float(data.get('price'), default=0.0)
count = safe_int(stats.get('trades'), default=0)
```

**연관 컴포넌트**:
- Backend: app/services/backtest_engine.py (백테스트 결과 변환)
- Backend: app/services/chart_data_service.py (차트 데이터 변환)
"""
import pandas as pd
from typing import Any


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    안전한 float 변환 (NaN, None, 변환 실패 처리)

    Args:
        value: 변환할 값
        default: 변환 실패 시 반환할 기본값

    Returns:
        float: 변환된 float 값 또는 기본값

    Examples:
        >>> safe_float(3.14)
        3.14
        >>> safe_float("3.14")
        3.14
        >>> safe_float(None)
        0.0
        >>> safe_float("invalid", default=-1.0)
        -1.0
        >>> safe_float(float('nan'))
        0.0
    """
    try:
        if pd.isna(value) or value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    안전한 int 변환 (NaN, None, 변환 실패 처리)

    Args:
        value: 변환할 값
        default: 변환 실패 시 반환할 기본값

    Returns:
        int: 변환된 int 값 또는 기본값

    Examples:
        >>> safe_int(42)
        42
        >>> safe_int("42")
        42
        >>> safe_int(3.7)
        3
        >>> safe_int(None)
        0
        >>> safe_int("invalid", default=-1)
        -1
        >>> safe_int(float('nan'))
        0
    """
    try:
        if pd.isna(value) or value is None:
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    안전한 str 변환 (None, 변환 실패 처리)

    Args:
        value: 변환할 값
        default: 변환 실패 시 반환할 기본값

    Returns:
        str: 변환된 str 값 또는 기본값

    Examples:
        >>> safe_str(42)
        '42'
        >>> safe_str(None)
        ''
        >>> safe_str(None, default="N/A")
        'N/A'
    """
    try:
        if value is None:
            return default
        return str(value)
    except (ValueError, TypeError):
        return default
