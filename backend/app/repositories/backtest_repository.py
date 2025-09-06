"""
백테스트 결과 저장/조회 Repository
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from abc import ABC, abstractmethod

from app.models.responses import BacktestResult


class BacktestRepositoryInterface(ABC):
    """백테스트 Repository 인터페이스"""
    
    @abstractmethod
    async def save_result(self, result: BacktestResult, user_id: Optional[str] = None) -> str:
        """백테스트 결과 저장"""
        pass
    
    @abstractmethod
    async def get_result(self, result_id: str) -> Optional[BacktestResult]:
        """백테스트 결과 조회"""
        pass
    
    @abstractmethod
    async def get_user_results(self, user_id: str, limit: int = 10) -> List[BacktestResult]:
        """사용자별 백테스트 결과 목록 조회"""
        pass
    
    @abstractmethod
    async def delete_result(self, result_id: str) -> bool:
        """백테스트 결과 삭제"""
        pass


class InMemoryBacktestRepository(BacktestRepositoryInterface):
    """인메모리 백테스트 Repository (개발/테스트용)"""
    
    def __init__(self):
        self._results: Dict[str, Dict[str, Any]] = {}
        self._user_results: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
    
    async def save_result(self, result: BacktestResult, user_id: Optional[str] = None) -> str:
        """백테스트 결과 저장"""
        try:
            # 결과 ID 생성 (timestamp 기반)
            result_id = f"bt_{int(datetime.now().timestamp() * 1000)}"
            
            # 결과 저장
            result_data = {
                'id': result_id,
                'result': result.dict(),
                'user_id': user_id,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            self._results[result_id] = result_data
            
            # 사용자별 결과 목록 업데이트
            if user_id:
                if user_id not in self._user_results:
                    self._user_results[user_id] = []
                self._user_results[user_id].append(result_id)
                
                # 최근 50개만 유지
                if len(self._user_results[user_id]) > 50:
                    oldest_id = self._user_results[user_id].pop(0)
                    if oldest_id in self._results:
                        del self._results[oldest_id]
            
            self.logger.info(f"백테스트 결과 저장 완료: {result_id}")
            return result_id
            
        except Exception as e:
            self.logger.error(f"백테스트 결과 저장 실패: {str(e)}")
            raise
    
    async def get_result(self, result_id: str) -> Optional[BacktestResult]:
        """백테스트 결과 조회"""
        try:
            if result_id not in self._results:
                return None
            
            result_data = self._results[result_id]['result']
            return BacktestResult(**result_data)
            
        except Exception as e:
            self.logger.error(f"백테스트 결과 조회 실패: {str(e)}")
            return None
    
    async def get_user_results(self, user_id: str, limit: int = 10) -> List[BacktestResult]:
        """사용자별 백테스트 결과 목록 조회"""
        try:
            if user_id not in self._user_results:
                return []
            
            result_ids = self._user_results[user_id][-limit:]  # 최신 limit개
            results = []
            
            for result_id in reversed(result_ids):  # 최신순
                if result_id in self._results:
                    result_data = self._results[result_id]['result']
                    results.append(BacktestResult(**result_data))
            
            return results
            
        except Exception as e:
            self.logger.error(f"사용자 백테스트 결과 조회 실패: {str(e)}")
            return []
    
    async def delete_result(self, result_id: str) -> bool:
        """백테스트 결과 삭제"""
        try:
            if result_id not in self._results:
                return False
            
            # 사용자별 목록에서도 제거
            result_data = self._results[result_id]
            user_id = result_data.get('user_id')
            
            if user_id and user_id in self._user_results:
                if result_id in self._user_results[user_id]:
                    self._user_results[user_id].remove(result_id)
            
            # 결과 삭제
            del self._results[result_id]
            
            self.logger.info(f"백테스트 결과 삭제 완료: {result_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"백테스트 결과 삭제 실패: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Repository 통계 정보"""
        return {
            'total_results': len(self._results),
            'total_users': len(self._user_results),
            'memory_usage_mb': len(str(self._results)) / (1024 * 1024)
        }


class MySQLBacktestRepository(BacktestRepositoryInterface):
    """MySQL 기반 백테스트 Repository (프로덕션용)"""
    
    def __init__(self, connection_pool=None):
        self.connection_pool = connection_pool
        self.logger = logging.getLogger(__name__)
    
    async def save_result(self, result: BacktestResult, user_id: Optional[str] = None) -> str:
        """MySQL에 백테스트 결과 저장"""
        # TODO: MySQL 연결 및 저장 로직 구현
        raise NotImplementedError("MySQL Repository는 향후 구현 예정")
    
    async def get_result(self, result_id: str) -> Optional[BacktestResult]:
        """MySQL에서 백테스트 결과 조회"""
        # TODO: MySQL 조회 로직 구현
        raise NotImplementedError("MySQL Repository는 향후 구현 예정")
    
    async def get_user_results(self, user_id: str, limit: int = 10) -> List[BacktestResult]:
        """MySQL에서 사용자별 백테스트 결과 목록 조회"""
        # TODO: MySQL 조회 로직 구현
        raise NotImplementedError("MySQL Repository는 향후 구현 예정")
    
    async def delete_result(self, result_id: str) -> bool:
        """MySQL에서 백테스트 결과 삭제"""
        # TODO: MySQL 삭제 로직 구현
        raise NotImplementedError("MySQL Repository는 향후 구현 예정")


# Repository 팩토리
class BacktestRepositoryFactory:
    """백테스트 Repository 팩토리"""
    
    @staticmethod
    def create(repository_type: str = "memory") -> BacktestRepositoryInterface:
        """Repository 인스턴스 생성"""
        if repository_type == "memory":
            return InMemoryBacktestRepository()
        elif repository_type == "mysql":
            return MySQLBacktestRepository()
        else:
            raise ValueError(f"지원하지 않는 Repository 타입: {repository_type}")


# 전역 인스턴스 (개발환경에서는 메모리, 프로덕션에서는 MySQL)
BacktestRepository = BacktestRepositoryFactory.create("memory")
backtest_repository = BacktestRepository
