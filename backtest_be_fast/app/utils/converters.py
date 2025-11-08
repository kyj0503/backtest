"""
타입 변환 유틸리티 (Type Conversion Utilities)

**역할**:
- 안전한 숫자 타입 변환 제공
- NaN, None, 잘못된 값 처리
- 단일 출처의 진실(Single Source of Truth) 제공

**주요 함수**:
1. safe_float(): 값을 안전하게 float로 변환
   - NaN, None 처리
   - TypeError, ValueError 예외 처리
   - 기본값 반환

2. safe_int(): 값을 안전하게 int로 변환
   - NaN, None 처리
   - TypeError, ValueError 예외 처리
   - 기본값 반환

**사용 예**:
```python
from app.utils.converters import safe_float, safe_int

# 일반 값 변환
value = safe_float(3.14)  # 3.14

# NaN 처리
import numpy as np
value = safe_float(np.nan, default=0.0)  # 0.0

# None 처리
value = safe_float(None, default=100.0)  # 100.0

# 오류 처리
value = safe_float("invalid", default=0.0)  # 0.0
```

**의존성**:
- pandas: NaN 체크
- numpy: NaN 처리

**연관 컴포넌트**:
- Backend: app/services/backtest_engine.py (통계 변환)
- Backend: app/services/validation_service.py (검증)
- Backend: app/services/portfolio_service.py (포트폴리오 계산)
"""
from typing import Any, TypeVar
import pandas as pd

T = TypeVar('T', float, int)


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    값을 안전하게 float로 변환합니다.

    NaN, None, 타입 오류 등을 처리하고 기본값을 반환합니다.

    Parameters
    ----------
    value : Any
        변환할 값
    default : float, optional
        변환 실패 시 반환할 기본값 (기본값: 0.0)

    Returns
    -------
    float
        변환된 float 값, 또는 변환 실패 시 기본값

    Examples
    --------
    >>> safe_float(3.14)
    3.14

    >>> safe_float("3.14")
    3.14

    >>> safe_float(float('nan'))
    0.0

    >>> safe_float(None, default=100.0)
    100.0

    >>> safe_float("invalid")
    0.0
    """
    try:
        # NaN 또는 None 체크
        if pd.isna(value) or value is None:
            return default
        # float로 변환
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    값을 안전하게 int로 변환합니다.

    NaN, None, 타입 오류 등을 처리하고 기본값을 반환합니다.

    Parameters
    ----------
    value : Any
        변환할 값
    default : int, optional
        변환 실패 시 반환할 기본값 (기본값: 0)

    Returns
    -------
    int
        변환된 int 값, 또는 변환 실패 시 기본값

    Examples
    --------
    >>> safe_int(42)
    42

    >>> safe_int("42")
    42

    >>> safe_int(3.99)
    3

    >>> safe_int(float('nan'))
    0

    >>> safe_int(None, default=100)
    100

    >>> safe_int("invalid")
    0
    """
    try:
        # NaN 또는 None 체크
        if pd.isna(value) or value is None:
            return default
        # int로 변환
        return int(value)
    except (ValueError, TypeError):
        return default
