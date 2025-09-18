"""
백테스트 이벤트 핸들러들
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.events import EventHandler, DomainEvent
from app.events.backtest_events import (
    BacktestStartedEvent, BacktestCompletedEvent, BacktestFailedEvent,
    StrategyOptimizationStartedEvent, StrategyOptimizationCompletedEvent
)

logger = logging.getLogger(__name__)


class BacktestLoggingHandler(EventHandler):
    """백테스트 이벤트 로깅 핸들러"""
    
    @property
    def event_types(self) -> List[str]:
        return [
            'BacktestStartedEvent',
            'BacktestCompletedEvent', 
            'BacktestFailedEvent',
            'StrategyOptimizationStartedEvent',
            'StrategyOptimizationCompletedEvent'
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """백테스트 이벤트 로깅"""
        try:
            if isinstance(event, BacktestStartedEvent):
                logger.info(f"백테스트 시작: {event.symbol} ({event.strategy}) [{event.start_date} ~ {event.end_date}]")
                
            elif isinstance(event, BacktestCompletedEvent):
                logger.info(f"백테스트 완료: {event.symbol} ({event.strategy}) - "
                           f"수익률: {event.annual_return:.2%}, 샤프: {event.sharpe_ratio:.2f}, "
                           f"거래: {event.trade_count}회, 시간: {event.execution_time_seconds:.2f}초")
                
            elif isinstance(event, BacktestFailedEvent):
                logger.error(f"백테스트 실패: {event.symbol} ({event.strategy}) - "
                            f"오류: {event.error_message} (타입: {event.error_type})")
                
            elif isinstance(event, StrategyOptimizationStartedEvent):
                logger.info(f"최적화 시작: {event.symbol} ({event.strategy}) - "
                           f"메트릭: {event.optimization_metric}")
                
            elif isinstance(event, StrategyOptimizationCompletedEvent):
                logger.info(f"최적화 완료: {event.symbol} ({event.strategy}) - "
                           f"최적값: {event.best_metric_value:.4f}, "
                           f"테스트: {event.total_combinations_tested}회, "
                           f"시간: {event.execution_time_seconds:.2f}초")
                
        except Exception as e:
            logger.error(f"백테스트 이벤트 로깅 중 오류: {str(e)}")


class BacktestMetricsHandler(EventHandler):
    """백테스트 메트릭 수집 핸들러"""
    
    def __init__(self):
        self.backtest_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.strategy_performance = {}
        self.symbol_performance = {}
    
    @property
    def event_types(self) -> List[str]:
        return ['BacktestCompletedEvent', 'BacktestFailedEvent']
    
    async def handle(self, event: DomainEvent) -> None:
        """백테스트 메트릭 수집"""
        try:
            if isinstance(event, BacktestCompletedEvent):
                self.backtest_count += 1
                self.success_count += 1
                self.total_execution_time += event.execution_time_seconds
                
                # 전략별 성과 추적
                strategy = event.strategy
                if strategy not in self.strategy_performance:
                    self.strategy_performance[strategy] = {
                        'count': 0,
                        'total_return': 0.0,
                        'avg_sharpe': 0.0,
                        'avg_trades': 0.0
                    }
                
                self.strategy_performance[strategy]['count'] += 1
                self.strategy_performance[strategy]['total_return'] += event.annual_return
                self.strategy_performance[strategy]['avg_sharpe'] += event.sharpe_ratio
                self.strategy_performance[strategy]['avg_trades'] += event.trade_count
                
                # 심볼별 성과 추적
                symbol = event.symbol
                if symbol not in self.symbol_performance:
                    self.symbol_performance[symbol] = {
                        'count': 0,
                        'avg_return': 0.0,
                        'best_strategy': None,
                        'best_return': float('-inf')
                    }
                
                self.symbol_performance[symbol]['count'] += 1
                self.symbol_performance[symbol]['avg_return'] += event.annual_return
                
                if event.annual_return > self.symbol_performance[symbol]['best_return']:
                    self.symbol_performance[symbol]['best_return'] = event.annual_return
                    self.symbol_performance[symbol]['best_strategy'] = strategy
                
            elif isinstance(event, BacktestFailedEvent):
                self.backtest_count += 1
                self.failure_count += 1
                self.total_execution_time += event.execution_time_seconds
                
        except Exception as e:
            logger.error(f"백테스트 메트릭 수집 중 오류: {str(e)}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """메트릭 요약 반환"""
        try:
            if self.backtest_count == 0:
                return {'no_data': True}
            
            # 전략별 평균 계산
            strategy_summary = {}
            for strategy, data in self.strategy_performance.items():
                count = data['count']
                if count > 0:
                    strategy_summary[strategy] = {
                        'count': count,
                        'avg_annual_return': data['total_return'] / count,
                        'avg_sharpe_ratio': data['avg_sharpe'] / count,
                        'avg_trade_count': data['avg_trades'] / count
                    }
            
            # 심볼별 평균 계산
            symbol_summary = {}
            for symbol, data in self.symbol_performance.items():
                count = data['count']
                if count > 0:
                    symbol_summary[symbol] = {
                        'count': count,
                        'avg_annual_return': data['avg_return'] / count,
                        'best_strategy': data['best_strategy'],
                        'best_return': data['best_return']
                    }
            
            return {
                'total_backtests': self.backtest_count,
                'success_rate': self.success_count / self.backtest_count,
                'failure_rate': self.failure_count / self.backtest_count,
                'avg_execution_time': self.total_execution_time / self.backtest_count,
                'strategy_performance': strategy_summary,
                'symbol_performance': symbol_summary
            }
            
        except Exception as e:
            logger.error(f"메트릭 요약 생성 중 오류: {str(e)}")
            return {'error': str(e)}


class BacktestNotificationHandler(EventHandler):
    """백테스트 알림 핸들러"""
    
    def __init__(self):
        self.notifications = []
        self.max_notifications = 100
    
    @property
    def event_types(self) -> List[str]:
        return ['BacktestCompletedEvent', 'BacktestFailedEvent', 'StrategyOptimizationCompletedEvent']
    
    async def handle(self, event: DomainEvent) -> None:
        """백테스트 알림 처리"""
        try:
            notification = None
            
            if isinstance(event, BacktestCompletedEvent):
                # 성과가 특히 좋거나 나쁜 경우 알림
                if event.annual_return > 0.3:  # 30% 이상
                    notification = {
                        'type': 'high_return',
                        'title': '높은 수익률 달성',
                        'message': f"{event.symbol} ({event.strategy}): {event.annual_return:.2%} 연간 수익률",
                        'severity': 'success',
                        'timestamp': event.occurred_at
                    }
                elif event.annual_return < -0.2:  # -20% 이하
                    notification = {
                        'type': 'high_loss',
                        'title': '높은 손실 발생',
                        'message': f"{event.symbol} ({event.strategy}): {event.annual_return:.2%} 연간 손실",
                        'severity': 'warning',
                        'timestamp': event.occurred_at
                    }
                elif event.sharpe_ratio > 2.0:  # 샤프 비율 2.0 이상
                    notification = {
                        'type': 'excellent_sharpe',
                        'title': '우수한 샤프 비율',
                        'message': f"{event.symbol} ({event.strategy}): 샤프 비율 {event.sharpe_ratio:.2f}",
                        'severity': 'info',
                        'timestamp': event.occurred_at
                    }
                
            elif isinstance(event, BacktestFailedEvent):
                notification = {
                    'type': 'backtest_failed',
                    'title': '백테스트 실패',
                    'message': f"{event.symbol} ({event.strategy}): {event.error_message}",
                    'severity': 'error',
                    'timestamp': event.occurred_at
                }
                
            elif isinstance(event, StrategyOptimizationCompletedEvent):
                notification = {
                    'type': 'optimization_completed',
                    'title': '최적화 완료',
                    'message': f"{event.symbol} ({event.strategy}): 최적값 {event.best_metric_value:.4f}",
                    'severity': 'info',
                    'timestamp': event.occurred_at
                }
            
            # 알림 저장
            if notification:
                self.notifications.append(notification)
                
                # 알림 개수 제한
                if len(self.notifications) > self.max_notifications:
                    self.notifications = self.notifications[-self.max_notifications:]
                
                logger.info(f"알림 생성: {notification['title']} - {notification['message']}")
                
        except Exception as e:
            logger.error(f"백테스트 알림 처리 중 오류: {str(e)}")
    
    def get_recent_notifications(self, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 알림 목록 반환"""
        return self.notifications[-limit:]
    
    def clear_notifications(self) -> None:
        """알림 목록 초기화"""
        self.notifications.clear()
        logger.info("백테스트 알림이 초기화되었습니다")
