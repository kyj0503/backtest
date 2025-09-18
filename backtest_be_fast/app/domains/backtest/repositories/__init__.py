"""
백테스트 도메인 Repository 인터페이스

실제 구현체는 app/repositories에 위치합니다.
"""

from app.repositories.backtest_repository import BacktestRepositoryInterface

__all__ = ["BacktestRepositoryInterface"]
