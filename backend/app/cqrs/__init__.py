"""
CQRS (Command Query Responsibility Segregation) 패턴 기본 구조
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar, Generic
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Type variables for generic typing
TCommand = TypeVar('TCommand')
TQuery = TypeVar('TQuery')
TResult = TypeVar('TResult')


class Command(ABC):
    """
    커맨드 기본 클래스
    
    시스템의 상태를 변경하는 작업을 나타냅니다.
    """
    
    def __init__(self, command_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.command_id = command_id or self._generate_id()
        self.timestamp = timestamp or datetime.utcnow()
    
    def _generate_id(self) -> str:
        """커맨드 ID 생성"""
        from uuid import uuid4
        return str(uuid4())
    
    @abstractmethod
    def validate(self) -> bool:
        """커맨드 유효성 검증"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """커맨드를 딕셔너리로 직렬화"""
        return {
            'command_id': self.command_id,
            'command_type': self.__class__.__name__,
            'timestamp': self.timestamp.isoformat(),
            **self._get_data()
        }
    
    @abstractmethod
    def _get_data(self) -> Dict[str, Any]:
        """커맨드별 데이터 반환"""
        pass


class Query(ABC):
    """
    쿼리 기본 클래스
    
    시스템의 데이터를 조회하는 작업을 나타냅니다.
    """
    
    def __init__(self, query_id: Optional[str] = None, timestamp: Optional[datetime] = None):
        self.query_id = query_id or self._generate_id()
        self.timestamp = timestamp or datetime.utcnow()
    
    def _generate_id(self) -> str:
        """쿼리 ID 생성"""
        from uuid import uuid4
        return str(uuid4())
    
    @abstractmethod
    def validate(self) -> bool:
        """쿼리 유효성 검증"""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """쿼리를 딕셔너리로 직렬화"""
        return {
            'query_id': self.query_id,
            'query_type': self.__class__.__name__,
            'timestamp': self.timestamp.isoformat(),
            **self._get_data()
        }
    
    @abstractmethod
    def _get_data(self) -> Dict[str, Any]:
        """쿼리별 데이터 반환"""
        pass


class CommandHandler(ABC, Generic[TCommand, TResult]):
    """커맨드 핸들러 기본 클래스"""
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """커맨드 처리"""
        pass


class QueryHandler(ABC, Generic[TQuery, TResult]):
    """쿼리 핸들러 기본 클래스"""
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """쿼리 처리"""
        pass


class CommandResult:
    """커맨드 실행 결과"""
    
    def __init__(self, success: bool, data: Any = None, error: Optional[str] = None, 
                 execution_time: Optional[float] = None):
        self.success = success
        self.data = data
        self.error = error
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }


class QueryResult:
    """쿼리 실행 결과"""
    
    def __init__(self, data: Any, metadata: Optional[Dict[str, Any]] = None,
                 execution_time: Optional[float] = None):
        self.data = data
        self.metadata = metadata or {}
        self.execution_time = execution_time
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'data': self.data,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp.isoformat()
        }


class CQRSBus:
    """CQRS 버스 - 커맨드와 쿼리 라우팅"""
    
    def __init__(self):
        self._command_handlers: Dict[str, CommandHandler] = {}
        self._query_handlers: Dict[str, QueryHandler] = {}
        self._command_history: List[Dict[str, Any]] = []
        self._query_history: List[Dict[str, Any]] = []
        self._max_history_size = 1000
    
    def register_command_handler(self, command_type: str, handler: CommandHandler) -> None:
        """커맨드 핸들러 등록"""
        self._command_handlers[command_type] = handler
        logger.info(f"커맨드 핸들러 등록: {command_type} -> {handler.__class__.__name__}")
    
    def register_query_handler(self, query_type: str, handler: QueryHandler) -> None:
        """쿼리 핸들러 등록"""
        self._query_handlers[query_type] = handler
        logger.info(f"쿼리 핸들러 등록: {query_type} -> {handler.__class__.__name__}")
    
    async def send_command(self, command: Command) -> CommandResult:
        """커맨드 전송 및 처리"""
        start_time = datetime.utcnow()
        command_type = command.__class__.__name__
        
        try:
            # 커맨드 유효성 검증
            if not command.validate():
                raise ValueError(f"Invalid command: {command_type}")
            
            # 핸들러 조회
            if command_type not in self._command_handlers:
                raise ValueError(f"No handler registered for command: {command_type}")
            
            handler = self._command_handlers[command_type]
            
            # 커맨드 처리
            logger.info(f"커맨드 처리 시작: {command_type} (ID: {command.command_id})")
            result_data = await handler.handle(command)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            result = CommandResult(success=True, data=result_data, execution_time=execution_time)
            
            # 히스토리에 추가
            self._add_command_to_history(command, result)
            
            logger.info(f"커맨드 처리 완료: {command_type} ({execution_time:.3f}초)")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            result = CommandResult(success=False, error=error_msg, execution_time=execution_time)
            
            # 실패한 커맨드도 히스토리에 추가
            self._add_command_to_history(command, result)
            
            logger.error(f"커맨드 처리 실패: {command_type} - {error_msg}")
            return result
    
    async def send_query(self, query: Query) -> QueryResult:
        """쿼리 전송 및 처리"""
        start_time = datetime.utcnow()
        query_type = query.__class__.__name__
        
        try:
            # 쿼리 유효성 검증
            if not query.validate():
                raise ValueError(f"Invalid query: {query_type}")
            
            # 핸들러 조회
            if query_type not in self._query_handlers:
                raise ValueError(f"No handler registered for query: {query_type}")
            
            handler = self._query_handlers[query_type]
            
            # 쿼리 처리
            logger.debug(f"쿼리 처리 시작: {query_type} (ID: {query.query_id})")
            result_data = await handler.handle(query)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            metadata = {
                'query_type': query_type,
                'query_id': query.query_id,
                'handler': handler.__class__.__name__
            }
            
            result = QueryResult(data=result_data, metadata=metadata, execution_time=execution_time)
            
            # 히스토리에 추가
            self._add_query_to_history(query, result)
            
            logger.debug(f"쿼리 처리 완료: {query_type} ({execution_time:.3f}초)")
            return result
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = str(e)
            
            metadata = {
                'query_type': query_type,
                'query_id': query.query_id,
                'error': error_msg
            }
            
            result = QueryResult(data=None, metadata=metadata, execution_time=execution_time)
            
            # 실패한 쿼리도 히스토리에 추가
            self._add_query_to_history(query, result)
            
            logger.error(f"쿼리 처리 실패: {query_type} - {error_msg}")
            raise Exception(f"Query processing failed: {error_msg}")
    
    def _add_command_to_history(self, command: Command, result: CommandResult) -> None:
        """커맨드를 히스토리에 추가"""
        entry = {
            'command': command.to_dict(),
            'result': result.to_dict(),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        self._command_history.append(entry)
        
        if len(self._command_history) > self._max_history_size:
            self._command_history = self._command_history[-self._max_history_size:]
    
    def _add_query_to_history(self, query: Query, result: QueryResult) -> None:
        """쿼리를 히스토리에 추가"""
        entry = {
            'query': query.to_dict(),
            'result': result.to_dict(),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        self._query_history.append(entry)
        
        if len(self._query_history) > self._max_history_size:
            self._query_history = self._query_history[-self._max_history_size:]
    
    def get_command_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """커맨드 히스토리 조회"""
        return self._command_history[-limit:]
    
    def get_query_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """쿼리 히스토리 조회"""
        return self._query_history[-limit:]
    
    def get_registered_handlers(self) -> Dict[str, Any]:
        """등록된 핸들러 목록 반환"""
        return {
            'commands': list(self._command_handlers.keys()),
            'queries': list(self._query_handlers.keys())
        }
    
    def clear_history(self) -> None:
        """히스토리 초기화"""
        self._command_history.clear()
        self._query_history.clear()
        logger.info("CQRS 히스토리가 초기화되었습니다")


# 전역 CQRS 버스 인스턴스
cqrs_bus = CQRSBus()
