"""
인터페이스 모듈

의존성 주입과 느슨한 결합을 위한 추상 인터페이스 정의
"""
from .data_source import DataSource, YFinanceDataSource, CachedDataSource

__all__ = [
    'DataSource',
    'YFinanceDataSource',
    'CachedDataSource'
]
