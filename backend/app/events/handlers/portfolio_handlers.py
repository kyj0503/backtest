"""
포트폴리오 이벤트 핸들러들
"""
import logging
from typing import List, Dict, Any
from datetime import datetime

from app.events import EventHandler, DomainEvent
from app.events.portfolio_events import (
    PortfolioCreatedEvent, PortfolioRebalancedEvent, PortfolioOptimizedEvent,
    AssetAddedToPortfolioEvent, AssetRemovedFromPortfolioEvent, RiskToleranceChangedEvent
)

logger = logging.getLogger(__name__)


class PortfolioLoggingHandler(EventHandler):
    """포트폴리오 이벤트 로깅 핸들러"""
    
    @property
    def event_types(self) -> List[str]:
        return [
            'PortfolioCreatedEvent',
            'PortfolioRebalancedEvent',
            'PortfolioOptimizedEvent',
            'AssetAddedToPortfolioEvent',
            'AssetRemovedFromPortfolioEvent',
            'RiskToleranceChangedEvent'
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """포트폴리오 이벤트 로깅"""
        try:
            if isinstance(event, PortfolioCreatedEvent):
                logger.info(f"포트폴리오 생성: '{event.name}' (ID: {event.portfolio_id}) - "
                           f"자산 {len(event.assets)}개, 총액: ${event.total_value:,.2f}")
                
            elif isinstance(event, PortfolioRebalancedEvent):
                logger.info(f"포트폴리오 리밸런싱: {event.portfolio_id} - "
                           f"트리거: {event.rebalancing_trigger}, "
                           f"거래비용: ${event.transaction_cost:.2f}, "
                           f"다변화 변화: {event.diversification_change:+.3f}")
                
            elif isinstance(event, PortfolioOptimizedEvent):
                logger.info(f"포트폴리오 최적화: {event.portfolio_id} - "
                           f"방법: {event.optimization_method}, "
                           f"리스크 허용도: {event.risk_tolerance:.2f}")
                
            elif isinstance(event, AssetAddedToPortfolioEvent):
                logger.info(f"자산 추가: {event.asset_symbol} ({event.asset_type}) → "
                           f"포트폴리오 {event.portfolio_id} - "
                           f"목표 비중: {event.target_weight:.2%}, 가치: ${event.added_value:,.2f}")
                
            elif isinstance(event, AssetRemovedFromPortfolioEvent):
                logger.info(f"자산 제거: {event.asset_symbol} ({event.asset_type}) ← "
                           f"포트폴리오 {event.portfolio_id} - "
                           f"이전 비중: {event.previous_weight:.2%}, 가치: ${event.removed_value:,.2f}")
                
            elif isinstance(event, RiskToleranceChangedEvent):
                logger.info(f"리스크 허용도 변경: 포트폴리오 {event.portfolio_id} - "
                           f"{event.old_risk_tolerance:.2f} → {event.new_risk_tolerance:.2f} "
                           f"(사유: {event.change_reason})")
                
        except Exception as e:
            logger.error(f"포트폴리오 이벤트 로깅 중 오류: {str(e)}")


class PortfolioAnalyticsHandler(EventHandler):
    """포트폴리오 분석 및 통계 핸들러"""
    
    def __init__(self):
        self.portfolio_stats = {}
        self.rebalancing_stats = {}
        self.optimization_stats = {}
        self.asset_popularity = {}
    
    @property
    def event_types(self) -> List[str]:
        return [
            'PortfolioCreatedEvent',
            'PortfolioRebalancedEvent', 
            'PortfolioOptimizedEvent',
            'AssetAddedToPortfolioEvent',
            'AssetRemovedFromPortfolioEvent'
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """포트폴리오 분석 데이터 수집"""
        try:
            if isinstance(event, PortfolioCreatedEvent):
                self.portfolio_stats[event.portfolio_id] = {
                    'created_at': event.occurred_at,
                    'name': event.name,
                    'initial_value': event.total_value,
                    'initial_asset_count': len(event.assets),
                    'rebalancing_count': 0,
                    'optimization_count': 0,
                    'asset_changes': 0
                }
                
                # 자산 인기도 추적
                for asset in event.assets:
                    symbol = asset.get('symbol', 'Unknown')
                    self.asset_popularity[symbol] = self.asset_popularity.get(symbol, 0) + 1
                
            elif isinstance(event, PortfolioRebalancedEvent):
                portfolio_id = event.portfolio_id
                
                # 포트폴리오 통계 업데이트
                if portfolio_id in self.portfolio_stats:
                    self.portfolio_stats[portfolio_id]['rebalancing_count'] += 1
                
                # 리밸런싱 통계
                if portfolio_id not in self.rebalancing_stats:
                    self.rebalancing_stats[portfolio_id] = {
                        'total_cost': 0.0,
                        'rebalancing_triggers': {},
                        'diversification_improvements': []
                    }
                
                self.rebalancing_stats[portfolio_id]['total_cost'] += event.transaction_cost
                
                trigger = event.rebalancing_trigger
                self.rebalancing_stats[portfolio_id]['rebalancing_triggers'][trigger] = \
                    self.rebalancing_stats[portfolio_id]['rebalancing_triggers'].get(trigger, 0) + 1
                
                self.rebalancing_stats[portfolio_id]['diversification_improvements'].append(
                    event.diversification_change
                )
                
            elif isinstance(event, PortfolioOptimizedEvent):
                portfolio_id = event.portfolio_id
                
                # 포트폴리오 통계 업데이트
                if portfolio_id in self.portfolio_stats:
                    self.portfolio_stats[portfolio_id]['optimization_count'] += 1
                
                # 최적화 통계
                if portfolio_id not in self.optimization_stats:
                    self.optimization_stats[portfolio_id] = {
                        'optimization_methods': {},
                        'risk_tolerance_history': [],
                        'improvements': []
                    }
                
                method = event.optimization_method
                self.optimization_stats[portfolio_id]['optimization_methods'][method] = \
                    self.optimization_stats[portfolio_id]['optimization_methods'].get(method, 0) + 1
                
                self.optimization_stats[portfolio_id]['risk_tolerance_history'].append(
                    event.risk_tolerance
                )
                
                self.optimization_stats[portfolio_id]['improvements'].append(
                    event.expected_improvement
                )
                
            elif isinstance(event, (AssetAddedToPortfolioEvent, AssetRemovedFromPortfolioEvent)):
                portfolio_id = event.portfolio_id
                
                # 자산 변경 횟수 증가
                if portfolio_id in self.portfolio_stats:
                    self.portfolio_stats[portfolio_id]['asset_changes'] += 1
                
                # 자산 인기도 업데이트
                symbol = event.asset_symbol
                if isinstance(event, AssetAddedToPortfolioEvent):
                    self.asset_popularity[symbol] = self.asset_popularity.get(symbol, 0) + 1
                
        except Exception as e:
            logger.error(f"포트폴리오 분석 데이터 수집 중 오류: {str(e)}")
    
    def get_portfolio_analytics(self, portfolio_id: Optional[str] = None) -> Dict[str, Any]:
        """포트폴리오 분석 결과 반환"""
        try:
            if portfolio_id:
                # 특정 포트폴리오 분석
                return {
                    'portfolio_stats': self.portfolio_stats.get(portfolio_id, {}),
                    'rebalancing_stats': self.rebalancing_stats.get(portfolio_id, {}),
                    'optimization_stats': self.optimization_stats.get(portfolio_id, {})
                }
            else:
                # 전체 분석
                total_portfolios = len(self.portfolio_stats)
                avg_rebalancing = sum(stats['rebalancing_count'] for stats in self.portfolio_stats.values()) / max(total_portfolios, 1)
                avg_optimization = sum(stats['optimization_count'] for stats in self.portfolio_stats.values()) / max(total_portfolios, 1)
                
                # 가장 인기있는 자산들
                popular_assets = sorted(self.asset_popularity.items(), key=lambda x: x[1], reverse=True)[:10]
                
                return {
                    'total_portfolios': total_portfolios,
                    'avg_rebalancing_per_portfolio': avg_rebalancing,
                    'avg_optimization_per_portfolio': avg_optimization,
                    'popular_assets': popular_assets,
                    'total_rebalancing_events': sum(len(stats.get('rebalancing_triggers', {})) 
                                                   for stats in self.rebalancing_stats.values())
                }
                
        except Exception as e:
            logger.error(f"포트폴리오 분석 결과 생성 중 오류: {str(e)}")
            return {'error': str(e)}


class PortfolioAlertHandler(EventHandler):
    """포트폴리오 경고 및 알림 핸들러"""
    
    def __init__(self):
        self.alerts = []
        self.max_alerts = 50
    
    @property
    def event_types(self) -> List[str]:
        return [
            'PortfolioRebalancedEvent',
            'PortfolioOptimizedEvent',
            'RiskToleranceChangedEvent'
        ]
    
    async def handle(self, event: DomainEvent) -> None:
        """포트폴리오 경고 처리"""
        try:
            alert = None
            
            if isinstance(event, PortfolioRebalancedEvent):
                # 높은 거래비용 경고
                if event.transaction_cost > 1000:  # $1000 이상
                    alert = {
                        'type': 'high_transaction_cost',
                        'title': '높은 거래비용 발생',
                        'message': f"포트폴리오 {event.portfolio_id}: ${event.transaction_cost:.2f} 거래비용",
                        'severity': 'warning',
                        'portfolio_id': event.portfolio_id,
                        'timestamp': event.occurred_at
                    }
                
                # 다변화 악화 경고
                elif event.diversification_change < -0.1:  # 10% 이상 악화
                    alert = {
                        'type': 'diversification_decline',
                        'title': '다변화 효과 악화',
                        'message': f"포트폴리오 {event.portfolio_id}: 다변화 점수 {event.diversification_change:+.3f}",
                        'severity': 'warning',
                        'portfolio_id': event.portfolio_id,
                        'timestamp': event.occurred_at
                    }
                
            elif isinstance(event, PortfolioOptimizedEvent):
                # 큰 가중치 변화 알림
                total_change = sum(abs(event.optimized_weights.get(asset, 0) - event.original_weights.get(asset, 0))
                                 for asset in set(list(event.optimized_weights.keys()) + list(event.original_weights.keys())))
                
                if total_change > 0.5:  # 50% 이상 변화
                    alert = {
                        'type': 'major_optimization_change',
                        'title': '대규모 포트폴리오 변경 권장',
                        'message': f"포트폴리오 {event.portfolio_id}: 총 {total_change:.1%} 가중치 변경 권장",
                        'severity': 'info',
                        'portfolio_id': event.portfolio_id,
                        'timestamp': event.occurred_at
                    }
                
            elif isinstance(event, RiskToleranceChangedEvent):
                # 큰 리스크 허용도 변화 알림
                change = abs(event.new_risk_tolerance - event.old_risk_tolerance)
                if change > 0.3:  # 30% 이상 변화
                    direction = "증가" if event.new_risk_tolerance > event.old_risk_tolerance else "감소"
                    alert = {
                        'type': 'risk_tolerance_major_change',
                        'title': f'리스크 허용도 대폭 {direction}',
                        'message': f"포트폴리오 {event.portfolio_id}: {event.old_risk_tolerance:.2f} → {event.new_risk_tolerance:.2f}",
                        'severity': 'info',
                        'portfolio_id': event.portfolio_id,
                        'timestamp': event.occurred_at
                    }
            
            # 경고 저장
            if alert:
                self.alerts.append(alert)
                
                # 경고 개수 제한
                if len(self.alerts) > self.max_alerts:
                    self.alerts = self.alerts[-self.max_alerts:]
                
                logger.info(f"포트폴리오 경고 생성: {alert['title']} - {alert['message']}")
                
        except Exception as e:
            logger.error(f"포트폴리오 경고 처리 중 오류: {str(e)}")
    
    def get_recent_alerts(self, portfolio_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """최근 경고 목록 반환"""
        alerts = self.alerts
        
        if portfolio_id:
            alerts = [alert for alert in alerts if alert.get('portfolio_id') == portfolio_id]
        
        return alerts[-limit:]
    
    def clear_alerts(self, portfolio_id: Optional[str] = None) -> None:
        """경고 목록 초기화"""
        if portfolio_id:
            self.alerts = [alert for alert in self.alerts if alert.get('portfolio_id') != portfolio_id]
            logger.info(f"포트폴리오 {portfolio_id}의 경고가 초기화되었습니다")
        else:
            self.alerts.clear()
            logger.info("모든 포트폴리오 경고가 초기화되었습니다")
