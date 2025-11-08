"""
의존성 주입 모듈

싱글톤 ServiceContainer를 통한 중앙 집중식 서비스 관리
"""
from .container import ServiceContainer, service_container, get_service_container

__all__ = [
    'ServiceContainer',
    'service_container',
    'get_service_container'
]
