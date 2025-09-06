"""
이벤트 시스템 초기화 및 설정
"""
import logging
from typing import Dict, Any, List

from app.events import event_bus
from app.events.handlers.backtest_handlers import (
    BacktestLoggingHandler, BacktestMetricsHandler, BacktestNotificationHandler
)
from app.events.handlers.portfolio_handlers import (
    PortfolioLoggingHandler, PortfolioAnalyticsHandler, PortfolioAlertHandler
)

logger = logging.getLogger(__name__)


class EventSystemManager:
    """이벤트 시스템 관리자"""
    
    def __init__(self):
        self.handlers = {}
        self.initialized = False
    
    def initialize(self) -> None:
        """이벤트 시스템 초기화"""
        if self.initialized:
            logger.warning("이벤트 시스템이 이미 초기화되었습니다")
            return
        
        try:
            # 백테스트 핸들러 등록
            self.handlers['backtest_logging'] = BacktestLoggingHandler()
            self.handlers['backtest_metrics'] = BacktestMetricsHandler()
            self.handlers['backtest_notification'] = BacktestNotificationHandler()
            
            # 포트폴리오 핸들러 등록
            self.handlers['portfolio_logging'] = PortfolioLoggingHandler()
            self.handlers['portfolio_analytics'] = PortfolioAnalyticsHandler()
            self.handlers['portfolio_alert'] = PortfolioAlertHandler()
            
            # 이벤트 버스에 핸들러 구독
            for handler_name, handler in self.handlers.items():
                event_bus.subscribe(handler)
                logger.info(f"이벤트 핸들러 '{handler_name}' 구독 완료")
            
            self.initialized = True
            logger.info("이벤트 시스템 초기화 완료")
            
        except Exception as e:
            logger.error(f"이벤트 시스템 초기화 중 오류: {str(e)}")
            raise
    
    def shutdown(self) -> None:
        """이벤트 시스템 종료"""
        if not self.initialized:
            return
        
        try:
            # 모든 핸들러 구독 해제
            for handler_name, handler in self.handlers.items():
                event_bus.unsubscribe(handler)
                logger.info(f"이벤트 핸들러 '{handler_name}' 구독 해제 완료")
            
            self.handlers.clear()
            self.initialized = False
            logger.info("이벤트 시스템 종료 완료")
            
        except Exception as e:
            logger.error(f"이벤트 시스템 종료 중 오류: {str(e)}")
    
    def get_handler(self, handler_name: str):
        """특정 핸들러 반환"""
        return self.handlers.get(handler_name)
    
    def get_system_status(self) -> Dict[str, Any]:
        """이벤트 시스템 상태 반환"""
        return {
            'initialized': self.initialized,
            'handlers_count': len(self.handlers),
            'registered_handlers': list(self.handlers.keys()),
            'event_bus_stats': {
                'total_event_types': len(event_bus.get_all_event_types()),
                'event_types': event_bus.get_all_event_types(),
                'handler_counts': {
                    event_type: event_bus.get_handler_count(event_type)
                    for event_type in event_bus.get_all_event_types()
                }
            }
        }
    
    def get_backtest_metrics(self) -> Dict[str, Any]:
        """백테스트 메트릭 반환"""
        metrics_handler = self.get_handler('backtest_metrics')
        if metrics_handler:
            return metrics_handler.get_metrics_summary()
        return {'error': 'Metrics handler not found'}
    
    def get_backtest_notifications(self, limit: int = 20) -> List[Dict[str, Any]]:
        """백테스트 알림 반환"""
        notification_handler = self.get_handler('backtest_notification')
        if notification_handler:
            return notification_handler.get_recent_notifications(limit)
        return []
    
    def get_portfolio_analytics(self, portfolio_id: str = None) -> Dict[str, Any]:
        """포트폴리오 분석 결과 반환"""
        analytics_handler = self.get_handler('portfolio_analytics')
        if analytics_handler:
            return analytics_handler.get_portfolio_analytics(portfolio_id)
        return {'error': 'Analytics handler not found'}
    
    def get_portfolio_alerts(self, portfolio_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """포트폴리오 경고 반환"""
        alert_handler = self.get_handler('portfolio_alert')
        if alert_handler:
            return alert_handler.get_recent_alerts(portfolio_id, limit)
        return []
    
    def clear_all_data(self) -> None:
        """모든 핸들러 데이터 초기화"""
        try:
            # 백테스트 알림 초기화
            notification_handler = self.get_handler('backtest_notification')
            if notification_handler:
                notification_handler.clear_notifications()
            
            # 포트폴리오 경고 초기화
            alert_handler = self.get_handler('portfolio_alert')
            if alert_handler:
                alert_handler.clear_alerts()
            
            # 이벤트 버스 히스토리 초기화
            event_bus.clear_history()
            
            logger.info("모든 이벤트 데이터가 초기화되었습니다")
            
        except Exception as e:
            logger.error(f"이벤트 데이터 초기화 중 오류: {str(e)}")


# 전역 이벤트 시스템 관리자 인스턴스
event_system_manager = EventSystemManager()
