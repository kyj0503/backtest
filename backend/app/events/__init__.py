"""
도메인 이벤트 기본 클래스 및 인터페이스
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Union
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class DomainEvent(ABC):
    """
    도메인 이벤트 기본 클래스
    
    모든 도메인 이벤트는 이 클래스를 상속받아야 합니다.
    """
    
    def __init__(self, event_id: Optional[str] = None, occurred_at: Optional[datetime] = None):
        """
        도메인 이벤트 초기화
        
        Args:
            event_id: 이벤트 고유 ID (None인 경우 자동 생성)
            occurred_at: 이벤트 발생 시각 (None인 경우 현재 시각)
        """
        self.event_id = event_id or str(uuid4())
        self.occurred_at = occurred_at or datetime.utcnow()
        self.event_type = self.__class__.__name__
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """이벤트를 딕셔너리로 직렬화"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DomainEvent':
        """딕셔너리에서 이벤트 복원"""
        pass
    
    def __str__(self) -> str:
        return f"{self.event_type}(id={self.event_id}, at={self.occurred_at})"
    
    def __repr__(self) -> str:
        return self.__str__()


class EventHandler(ABC):
    """
    이벤트 핸들러 기본 클래스
    """
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """이벤트 처리"""
        pass
    
    @property
    @abstractmethod
    def event_types(self) -> List[str]:
        """처리 가능한 이벤트 타입 목록"""
        pass


class EventBus:
    """
    이벤트 버스 - 이벤트 발행 및 구독 관리
    """
    
    def __init__(self):
        """이벤트 버스 초기화"""
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_history: List[DomainEvent] = []
        self._max_history_size = 1000
        
        logger.info("EventBus가 초기화되었습니다")
    
    def subscribe(self, handler: EventHandler) -> None:
        """
        이벤트 핸들러 구독
        
        Args:
            handler: 구독할 이벤트 핸들러
        """
        for event_type in handler.event_types:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)
                logger.info(f"Handler {handler.__class__.__name__}가 {event_type} 이벤트에 구독되었습니다")
    
    def unsubscribe(self, handler: EventHandler) -> None:
        """
        이벤트 핸들러 구독 해제
        
        Args:
            handler: 구독 해제할 이벤트 핸들러
        """
        for event_type in handler.event_types:
            if event_type in self._handlers and handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)
                logger.info(f"Handler {handler.__class__.__name__}가 {event_type} 이벤트에서 구독 해제되었습니다")
    
    async def publish(self, event: DomainEvent) -> None:
        """
        이벤트 발행
        
        Args:
            event: 발행할 도메인 이벤트
        """
        try:
            # 이벤트 히스토리에 추가
            self._add_to_history(event)
            
            # 해당 이벤트 타입의 핸들러들에게 이벤트 전달
            event_type = event.event_type
            if event_type in self._handlers:
                handlers = self._handlers[event_type].copy()
                
                logger.info(f"이벤트 {event}를 {len(handlers)}개 핸들러에게 발행합니다")
                
                for handler in handlers:
                    try:
                        await handler.handle(event)
                        logger.debug(f"Handler {handler.__class__.__name__}가 이벤트를 성공적으로 처리했습니다")
                    except Exception as e:
                        logger.error(f"Handler {handler.__class__.__name__}에서 이벤트 처리 중 오류: {str(e)}")
                        # 한 핸들러의 실패가 다른 핸들러에 영향을 주지 않도록 계속 진행
            else:
                logger.debug(f"이벤트 타입 {event_type}에 대한 핸들러가 없습니다")
                
        except Exception as e:
            logger.error(f"이벤트 발행 중 오류: {str(e)}")
            raise
    
    def _add_to_history(self, event: DomainEvent) -> None:
        """이벤트를 히스토리에 추가"""
        self._event_history.append(event)
        
        # 히스토리 크기 제한
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
    
    def get_event_history(self, event_type: Optional[str] = None, limit: int = 100) -> List[DomainEvent]:
        """
        이벤트 히스토리 조회
        
        Args:
            event_type: 특정 이벤트 타입 필터 (None인 경우 모든 타입)
            limit: 반환할 최대 이벤트 수
            
        Returns:
            이벤트 리스트 (최신 순)
        """
        events = self._event_history
        
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        return events[-limit:]
    
    def get_handler_count(self, event_type: str) -> int:
        """특정 이벤트 타입의 핸들러 수 반환"""
        return len(self._handlers.get(event_type, []))
    
    def get_all_event_types(self) -> List[str]:
        """등록된 모든 이벤트 타입 반환"""
        return list(self._handlers.keys())
    
    def clear_history(self) -> None:
        """이벤트 히스토리 초기화"""
        self._event_history.clear()
        logger.info("이벤트 히스토리가 초기화되었습니다")


# 전역 이벤트 버스 인스턴스
event_bus = EventBus()
