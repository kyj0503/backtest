"""
CQRS 커맨드 핸들러들
"""
from typing import Any, Dict, Optional, List
import asyncio
from datetime import datetime

from app.cqrs import CommandHandler
from app.cqrs.commands import (
    RunBacktestCommand, RunPortfolioBacktestCommand, OptimizeStrategyCommand,
    OptimizePortfolioCommand, RebalancePortfolioCommand, CreatePortfolioCommand
)
from app.services.enhanced_backtest_service import EnhancedBacktestService
from app.services.enhanced_portfolio_service import EnhancedPortfolioService
from app.events import EventBus
from app.events.backtest_events import (
    BacktestStartedEvent, BacktestCompletedEvent, BacktestFailedEvent,
    OptimizationStartedEvent, OptimizationCompletedEvent
)
from app.events.portfolio_events import (
    PortfolioCreatedEvent, PortfolioOptimizedEvent, PortfolioRebalancedEvent,
    PortfolioAnalyzedEvent, PortfolioUpdatedEvent, PortfolioDeletedEvent
)


class RunBacktestCommandHandler(CommandHandler[RunBacktestCommand]):
    """백테스트 실행 커맨드 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService, event_bus: EventBus):
        self.backtest_service = backtest_service
        self.event_bus = event_bus
    
    async def handle(self, command: RunBacktestCommand) -> Dict[str, Any]:
        """백테스트 실행"""
        try:
            # 백테스트 시작 이벤트 발행
            start_event = BacktestStartedEvent(
                backtest_id=command.command_id,
                symbol=command.symbol,
                strategy=command.strategy,
                start_date=command.start_date,
                end_date=command.end_date
            )
            await self.event_bus.publish(start_event)
            
            # 백테스트 실행
            if command.use_enhanced_analysis:
                result = await asyncio.to_thread(
                    self.backtest_service.run_enhanced_backtest,
                    command.symbol,
                    command.strategy,
                    command.start_date,
                    command.end_date,
                    command.strategy_params,
                    command.commission,
                    command.initial_cash
                )
            else:
                result = await asyncio.to_thread(
                    self.backtest_service.run_backtest,
                    command.symbol,
                    command.strategy,
                    command.start_date,
                    command.end_date,
                    command.strategy_params,
                    command.commission,
                    command.initial_cash
                )
            
            # 백테스트 완료 이벤트 발행
            complete_event = BacktestCompletedEvent(
                backtest_id=command.command_id,
                symbol=command.symbol,
                strategy=command.strategy,
                final_value=result.get('final_value', 0),
                total_return=result.get('total_return', 0),
                max_drawdown=result.get('max_drawdown', 0),
                sharpe_ratio=result.get('sharpe_ratio', 0),
                execution_time=datetime.now()
            )
            await self.event_bus.publish(complete_event)
            
            return {
                'success': True,
                'backtest_id': command.command_id,
                'result': result
            }
            
        except Exception as e:
            # 백테스트 실패 이벤트 발행
            failed_event = BacktestFailedEvent(
                backtest_id=command.command_id,
                symbol=command.symbol,
                strategy=command.strategy,
                error_message=str(e),
                error_type=type(e).__name__
            )
            await self.event_bus.publish(failed_event)
            
            return {
                'success': False,
                'error': str(e),
                'backtest_id': command.command_id
            }


class RunPortfolioBacktestCommandHandler(CommandHandler[RunPortfolioBacktestCommand]):
    """포트폴리오 백테스트 실행 커맨드 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService, event_bus: EventBus):
        self.portfolio_service = portfolio_service
        self.event_bus = event_bus
    
    async def handle(self, command: RunPortfolioBacktestCommand) -> Dict[str, Any]:
        """포트폴리오 백테스트 실행"""
        try:
            # 포트폴리오 분석 시작 이벤트
            analysis_event = PortfolioAnalyzedEvent(
                portfolio_id=command.portfolio_name,
                analysis_type='backtest',
                metrics={'total_investment': command.total_investment}
            )
            await self.event_bus.publish(analysis_event)
            
            # 포트폴리오 백테스트 실행
            if command.use_enhanced_analysis:
                result = await asyncio.to_thread(
                    self.portfolio_service.run_enhanced_portfolio_backtest,
                    command.portfolio_name,
                    command.stocks,
                    command.start_date,
                    command.end_date,
                    command.total_investment,
                    command.rebalancing_frequency,
                    command.commission
                )
            else:
                result = await asyncio.to_thread(
                    self.portfolio_service.run_portfolio_backtest,
                    command.portfolio_name,
                    command.stocks,
                    command.start_date,
                    command.end_date,
                    command.total_investment,
                    command.rebalancing_frequency,
                    command.commission
                )
            
            return {
                'success': True,
                'portfolio_id': command.portfolio_name,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_id': command.portfolio_name
            }


class OptimizeStrategyCommandHandler(CommandHandler[OptimizeStrategyCommand]):
    """전략 최적화 커맨드 핸들러"""
    
    def __init__(self, backtest_service: EnhancedBacktestService, event_bus: EventBus):
        self.backtest_service = backtest_service
        self.event_bus = event_bus
    
    async def handle(self, command: OptimizeStrategyCommand) -> Dict[str, Any]:
        """전략 최적화 실행"""
        try:
            # 최적화 시작 이벤트 발행
            start_event = OptimizationStartedEvent(
                optimization_id=command.command_id,
                symbol=command.symbol,
                strategy=command.strategy,
                parameter_ranges=command.parameter_ranges,
                max_combinations=command.max_combinations
            )
            await self.event_bus.publish(start_event)
            
            # 최적화 실행
            result = await asyncio.to_thread(
                self.backtest_service.optimize_strategy,
                command.symbol,
                command.strategy,
                command.start_date,
                command.end_date,
                command.parameter_ranges,
                command.optimization_metric,
                command.max_combinations
            )
            
            # 최적화 완료 이벤트 발행
            complete_event = OptimizationCompletedEvent(
                optimization_id=command.command_id,
                symbol=command.symbol,
                strategy=command.strategy,
                best_parameters=result.get('best_parameters', {}),
                best_score=result.get('best_score', 0),
                total_combinations=result.get('total_combinations', 0)
            )
            await self.event_bus.publish(complete_event)
            
            return {
                'success': True,
                'optimization_id': command.command_id,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'optimization_id': command.command_id
            }


class OptimizePortfolioCommandHandler(CommandHandler[OptimizePortfolioCommand]):
    """포트폴리오 최적화 커맨드 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService, event_bus: EventBus):
        self.portfolio_service = portfolio_service
        self.event_bus = event_bus
    
    async def handle(self, command: OptimizePortfolioCommand) -> Dict[str, Any]:
        """포트폴리오 최적화 실행"""
        try:
            # 최적화 실행
            result = await asyncio.to_thread(
                self.portfolio_service.optimize_portfolio,
                command.portfolio_id,
                command.assets,
                command.risk_tolerance,
                command.optimization_method,
                command.constraints
            )
            
            # 포트폴리오 최적화 이벤트 발행
            optimized_event = PortfolioOptimizedEvent(
                portfolio_id=command.portfolio_id,
                optimization_method=command.optimization_method,
                risk_tolerance=command.risk_tolerance,
                optimized_weights=result.get('optimized_weights', {}),
                expected_return=result.get('expected_return', 0),
                expected_risk=result.get('expected_risk', 0)
            )
            await self.event_bus.publish(optimized_event)
            
            return {
                'success': True,
                'portfolio_id': command.portfolio_id,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_id': command.portfolio_id
            }


class RebalancePortfolioCommandHandler(CommandHandler[RebalancePortfolioCommand]):
    """포트폴리오 리밸런싱 커맨드 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService, event_bus: EventBus):
        self.portfolio_service = portfolio_service
        self.event_bus = event_bus
    
    async def handle(self, command: RebalancePortfolioCommand) -> Dict[str, Any]:
        """포트폴리오 리밸런싱 실행"""
        try:
            # 리밸런싱 실행
            result = await asyncio.to_thread(
                self.portfolio_service.rebalance_portfolio,
                command.portfolio_id,
                command.target_weights,
                command.transaction_cost_limit
            )
            
            # 포트폴리오 리밸런싱 이벤트 발행
            rebalanced_event = PortfolioRebalancedEvent(
                portfolio_id=command.portfolio_id,
                old_weights=result.get('old_weights', {}),
                new_weights=command.target_weights,
                rebalancing_trigger=command.rebalancing_trigger,
                transaction_costs=result.get('transaction_costs', 0),
                trades_executed=result.get('trades_executed', [])
            )
            await self.event_bus.publish(rebalanced_event)
            
            return {
                'success': True,
                'portfolio_id': command.portfolio_id,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_id': command.portfolio_id
            }


class CreatePortfolioCommandHandler(CommandHandler[CreatePortfolioCommand]):
    """포트폴리오 생성 커맨드 핸들러"""
    
    def __init__(self, portfolio_service: EnhancedPortfolioService, event_bus: EventBus):
        self.portfolio_service = portfolio_service
        self.event_bus = event_bus
    
    async def handle(self, command: CreatePortfolioCommand) -> Dict[str, Any]:
        """포트폴리오 생성"""
        try:
            # 포트폴리오 생성
            result = await asyncio.to_thread(
                self.portfolio_service.create_portfolio,
                command.name,
                command.assets,
                command.total_value,
                command.creator_id
            )
            
            # 포트폴리오 생성 이벤트 발행
            created_event = PortfolioCreatedEvent(
                portfolio_id=result.get('portfolio_id'),
                name=command.name,
                assets=command.assets,
                total_value=command.total_value,
                creator_id=command.creator_id
            )
            await self.event_bus.publish(created_event)
            
            return {
                'success': True,
                'portfolio_id': result.get('portfolio_id'),
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'portfolio_name': command.name
            }
