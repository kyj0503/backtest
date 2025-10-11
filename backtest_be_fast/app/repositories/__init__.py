"""
Repository 패턴 구현
데이터 액세스 로직을 비즈니스 로직에서 분리
"""

from .data_repository import DataRepository, data_repository

__all__ = [
    'DataRepository',
    'data_repository',
]
