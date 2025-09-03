import pandas as pd
import numpy as np

def recursive_serialize(obj):
    """객체를 JSON 직렬화 가능한 형태로 변환"""
    # 기본 JSON 직렬화 가능한 타입이면 그대로 반환
    if isinstance(obj, (str, int, bool)) or obj is None:
        return obj
    # Float 값 처리: inf, -inf, NaN 등을 문자열로 변환
    if isinstance(obj, float):
        if pd.isna(obj) or np.isnan(obj):
            return "NaN"
        if np.isinf(obj):
            return "Infinity" if obj > 0 else "-Infinity"
        return obj
    # dict인 경우, 모든 값을 재귀적으로 직렬화
    if isinstance(obj, dict):
        return {k: recursive_serialize(v) for k, v in obj.items()}
    # list, tuple, set 인 경우 각각 순회
    if isinstance(obj, (list, tuple, set)):
        return [recursive_serialize(v) for v in obj]
    # Pandas DataFrame 은 dict로 변환 (리스트의 레코드 형태)
    if isinstance(obj, pd.DataFrame):
        return obj.reset_index(drop=True).to_dict(orient='records')
    # Pandas Series 은 리스트로 변환
    if isinstance(obj, pd.Series):
        return obj.tolist()
    # Pandas Index는 리스트로 변환
    if isinstance(obj, pd.Index):
        return list(obj)
    # datetime 또는 Timestamp 객체
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    # 위에 해당하지 않는 경우, str()로 변환
    return str(obj) 