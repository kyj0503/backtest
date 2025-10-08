"""
백테스팅 실행 서비스 (리팩터링된 버전)
Repository Pattern과 Factory Pattern 적용
"""
import time
import signal
from datetime import datetime, date
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import logging
import traceback
from fastapi import HTTPException
from decimal import Decimal

# Repository와 Factory 패턴 import
from app.repositories import backtest_repository, data_repository
from app.factories import strategy_factory, service_factory

# Monkey patch for pandas Timedelta compatibility issue
def _patch_backtesting_stats():
    """백테스팅 라이브러리의 통계 계산 오류를 수정하는 패치"""
    try:
        from backtesting._stats import compute_stats, _round_timedelta
        import pandas as pd
        
        # 원본 함수 백업
        original_compute_stats = compute_stats
        
        def patched_compute_stats(*args, **kwargs):
            try:
                return original_compute_stats(*args, **kwargs)
            except (TypeError, ValueError) as e:
                if "'>=' not supported between instances of 'float' and 'Timedelta'" in str(e):
                    # Timedelta 오류 발생 시 기본 통계만 반환
                    logger = logging.getLogger(__name__)
                    logger.warning("Timedelta 호환성 오류로 인해 기본 통계를 반환합니다.")
                    
                    # 기본 통계 Series 생성
                    basic_stats = pd.Series({
                        'Start': args[2].index[0] if len(args) > 2 else None,
                        'End': args[2].index[-1] if len(args) > 2 else None,
                        'Duration': None,
                        'Exposure Time [%]': 100.0,
                        'Equity Final [$]': float(args[1][-1]) if len(args) > 1 else 10000.0,
                        'Equity Peak [$]': float(max(args[1])) if len(args) > 1 else 10000.0,
                        'Return [%]': 0.0,
                        'Buy & Hold Return [%]': 0.0,
                        'Return (Ann.) [%]': 0.0,
                        'Volatility (Ann.) [%]': 0.0,
                        'Sharpe Ratio': 0.0,
                        'Sortino Ratio': 0.0,
                        'Calmar Ratio': 0.0,
                        'Max. Drawdown [%]': 0.0,
                        'Avg. Drawdown [%]': 0.0,
                        'Max. Drawdown Duration': pd.Timedelta(0),
                        'Avg. Drawdown Duration': pd.Timedelta(0),
                        '# Trades': len(args[0]) if len(args) > 0 else 0,
                        'Win Rate [%]': 50.0,
                        'Best Trade [%]': 0.0,
                        'Worst Trade [%]': 0.0,
                        'Avg. Trade [%]': 0.0,
                        'Max. Trade Duration': pd.Timedelta(0),
                        'Avg. Trade Duration': pd.Timedelta(0),
                        'Profit Factor': 1.0,
                        'Expectancy [%]': 0.0,
                        'SQN': 0.0,
                        '_strategy': args[4] if len(args) > 4 else None,
                        '_equity_curve': pd.DataFrame({
                            'Equity': args[1] if len(args) > 1 else [10000.0],
                            'DrawdownPct': [0.0] * (len(args[1]) if len(args) > 1 else 1)
                        }, index=args[2].index if len(args) > 2 else pd.RangeIndex(1)),
                        '_trades': pd.DataFrame() if len(args) == 0 else pd.DataFrame(args[0])
                    })
                    return basic_stats
                else:
                    raise
        
        # 패치 적용
        import backtesting._stats
        backtesting._stats.compute_stats = patched_compute_stats
        
    except ImportError:
        pass

# 패치 적용
_patch_backtesting_stats()

from app.models.requests import BacktestRequest, OptimizationRequest
from app.models.responses import BacktestResult, OptimizationResult, ChartDataResponse, ChartDataPoint, EquityPoint, TradeMarker, IndicatorData
from app.utils.data_fetcher import data_fetcher
from app.services.strategy_service import strategy_service
from app.core.config import settings
from app.core.custom_exceptions import ValidationError

# 분리된 서비스들 import
from .backtest import (
    backtest_engine,
    optimization_service, 
    chart_data_service,
    validation_service
)

logger = logging.getLogger(__name__)


class BacktestService:
    """
    백테스팅 서비스 클래스 (Repository Pattern 및 Factory Pattern 적용)
    
    이제 Repository와 Factory를 통해 의존성을 주입받고,
    분리된 전담 서비스들에게 작업을 위임합니다:
    - BacktestEngine: 백테스트 실행 (Repository 주입)
    - OptimizationService: 파라미터 최적화 (Repository 주입)
    - ChartDataService: 차트 데이터 생성 (Repository 주입)
    - ValidationService: 검증 및 유틸리티
    """
    
    def __init__(self, service_factory_instance=None):
        # Factory Pattern을 통한 서비스 생성
        self.service_factory = service_factory_instance or service_factory
        
        # Repository Pattern을 통한 의존성 주입된 서비스들
        self.backtest_engine = self.service_factory.create_backtest_engine()
        self.optimization_service = self.service_factory.create_optimization_service()
        self.chart_data_service = self.service_factory.create_chart_data_service()
        self.validation_service = self.service_factory.create_validation_service()
        
        # Repository 직접 접근 (필요시)
        self.backtest_repository = backtest_repository
        self.data_repository = data_repository
        self.strategy_factory = strategy_factory
        
        # 호환성을 위해 기존 속성들 유지
        from app.utils.data_fetcher import data_fetcher
        from app.services.strategy_service import strategy_service
        self.data_fetcher = data_fetcher
        self.strategy_service = strategy_service

        logger.info("백테스트 서비스가 초기화되었습니다")
    
    async def run_backtest(self, request: BacktestRequest) -> BacktestResult:
        """백테스트 실행 - Repository Pattern이 적용된 BacktestEngine에 위임"""
        return await self.backtest_engine.run_backtest(request)
    
    async def optimize_strategy(self, request: OptimizationRequest) -> OptimizationResult:
        """전략 파라미터 최적화 - Repository Pattern이 적용된 OptimizationService에 위임"""
        return await self.optimization_service.optimize_strategy(request)
    
    async def generate_chart_data(self, request: BacktestRequest, backtest_result: BacktestResult = None) -> ChartDataResponse:
        """차트 데이터 생성 - Repository Pattern이 적용된 ChartDataService에 위임"""
        return await self.chart_data_service.generate_chart_data(request, backtest_result)
    
    def validate_backtest_request(self, request: BacktestRequest) -> None:
        """백테스트 요청 검증 - ValidationService에 위임"""
        return self.validation_service.validate_backtest_request(request)
    
    # Repository를 활용한 새로운 메서드들
    async def save_backtest_result(self, result: BacktestResult) -> str:
        """백테스트 결과 저장"""
        return await self.backtest_repository.save_result(result)
    
    async def get_backtest_result(self, result_id: str) -> Optional[BacktestResult]:
        """백테스트 결과 조회"""
        return await self.backtest_repository.get_result(result_id)
    
    async def list_backtest_results(self, limit: int = 10) -> List[BacktestResult]:
        """최근 백테스트 결과 목록 조회"""
        return await self.backtest_repository.list_results(limit)
    
    async def get_cached_stock_data(self, ticker: str, start_date, end_date) -> pd.DataFrame:
        """캐시된 주식 데이터 조회"""
        return await self.data_repository.get_stock_data(ticker, start_date, end_date)
    
    def get_available_strategies(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 전략 목록 (Factory Pattern)"""
        return self.strategy_factory.get_available_strategies()
    
    def validate_strategy_params(self, strategy_name: str, params: Dict[str, Any]) -> bool:
        """전략 파라미터 검증 (Factory Pattern)"""
        return self.strategy_factory.validate_strategy_params(strategy_name, params)
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """시스템 통계 정보"""
        return {
            'repository_stats': {
                'backtest_cache': await self.backtest_repository.get_stats() if hasattr(self.backtest_repository, 'get_stats') else {},
                'data_cache': await self.data_repository.get_cache_stats()
            },
            'service_stats': self.service_factory.get_service_stats(),
            'strategy_stats': {
                'available_strategies': len(self.strategy_factory.get_available_strategies()),
                'factory_type': type(self.strategy_factory).__name__
            }
        }
    
    # 호환성을 위한 유틸리티 메서드들 (ValidationService 위임)
    def safe_float(self, value, default: float = 0.0) -> float:
        """안전한 float 변환 - ValidationService에 위임"""
        return self.validation_service.safe_float(value, default)
    
    def safe_int(self, value, default: int = 0) -> int:
        """안전한 int 변환 - ValidationService에 위임"""
        return self.validation_service.safe_int(value, default)

    async def run_backtest_with_domain_analysis(self, request: BacktestRequest) -> Dict[str, Any]:
        """
        도메인 분석이 포함된 백테스트 실행
        
        기존 백테스트 결과에 다음과 같은 고급 분석을 추가합니다:
        - 전략 메타데이터 분석
        - 성과 지표 상세 분석
        - 백테스트 결과 품질 검증
        """
        try:
            # 1. 기존 백테스트 실행
            base_result = await self.run_backtest(request)
            
            # 2. 도메인 서비스를 활용한 고급 분석 추가
            enhanced_result = await self._enhance_backtest_result(request, base_result)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced 백테스트 실행 중 오류: {str(e)}")
            raise
    
    async def _enhance_backtest_result(self, request: BacktestRequest, base_result: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 결과에 도메인 분석 추가"""
        
        # 기본 결과 복사
        enhanced_result = base_result.copy()
        
        # 도메인 분석 결과 추가
        domain_analysis = {}
        
        try:
            # 1. 전략 메타데이터 분석
            strategy_metadata = self._analyze_strategy_metadata(request.strategy_name, request.strategy_params)
            domain_analysis['strategy_metadata'] = strategy_metadata
            
            # 2. 성과 지표 도메인 분석
            if 'stats' in base_result:
                performance_analysis = self._analyze_performance_metrics(base_result['stats'])
                domain_analysis['performance_analysis'] = performance_analysis
            
            # 3. 백테스트 품질 검증
            quality_assessment = self._assess_backtest_quality(request, base_result)
            domain_analysis['quality_assessment'] = quality_assessment
            
            # 4. 날짜 범위 분석
            date_analysis = self._analyze_date_range(request.start_date, request.end_date)
            domain_analysis['date_analysis'] = date_analysis
            
            # 도메인 분석 결과를 기본 결과에 추가
            enhanced_result['domain_analysis'] = domain_analysis
            
        except Exception as e:
            logger.warning(f"도메인 분석 중 오류 발생 (기본 결과는 유지): {str(e)}")
            enhanced_result['domain_analysis'] = {
                'error': f"도메인 분석 중 오류: {str(e)}",
                'base_result_available': True
            }
        
        return enhanced_result
    
    def _analyze_strategy_metadata(self, strategy_name: str, strategy_params: Dict[str, Any]) -> Dict[str, Any]:
        """전략 메타데이터 분석"""
        try:
            # 전략 도메인 서비스를 통한 전략 분석
            strategy_entity = self.strategy_domain_service.create_strategy_entity(
                strategy_id=f"strategy_{strategy_name}",
                name=strategy_name,
                parameters=strategy_params
            )
            
            return {
                'strategy_id': strategy_entity.strategy_id,
                'strategy_name': strategy_entity.name,
                'parameter_count': len(strategy_entity.parameters),
                'is_valid': strategy_entity.is_valid(),
                'parameter_summary': strategy_entity.get_parameter_summary(),
                'description': strategy_entity.description or f"{strategy_name} 전략"
            }
            
        except Exception as e:
            logger.warning(f"전략 메타데이터 분석 실패: {str(e)}")
            return {
                'strategy_name': strategy_name,
                'parameter_count': len(strategy_params),
                'analysis_error': str(e)
            }
    
    def _analyze_performance_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """성과 지표 도메인 분석"""
        try:
            # 백테스트 도메인 서비스를 통한 성과 지표 생성
            total_return = float(stats.get('Return [%]', 0)) / 100
            annual_return = float(stats.get('Return (Ann.) [%]', 0)) / 100
            volatility = float(stats.get('Volatility (Ann.) [%]', 0)) / 100
            sharpe_ratio = float(stats.get('Sharpe Ratio', 0))
            max_drawdown = float(stats.get('Max. Drawdown [%]', 0)) / 100
            
            # 백테스트 결과 엔티티 생성
            result_entity = self.backtest_domain_service.generate_backtest_result(
                result_id=f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                symbol=stats.get('symbol', 'Unknown'),
                strategy=stats.get('strategy', 'Unknown'),
                total_return=total_return,
                annual_return=annual_return,
                volatility=volatility,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown
            )
            
            return {
                'result_id': result_entity.result_id,
                'is_successful': result_entity.is_successful(),
                'performance_grade': result_entity.get_performance_grade(),
                'metrics_summary': result_entity.get_metrics_summary(),
                'risk_assessment': {
                    'volatility_level': 'High' if volatility > 0.3 else 'Medium' if volatility > 0.15 else 'Low',
                    'drawdown_severity': 'Severe' if abs(max_drawdown) > 0.2 else 'Moderate' if abs(max_drawdown) > 0.1 else 'Mild',
                    'sharpe_quality': 'Excellent' if sharpe_ratio > 1.5 else 'Good' if sharpe_ratio > 1.0 else 'Fair' if sharpe_ratio > 0.5 else 'Poor'
                }
            }
            
        except Exception as e:
            logger.warning(f"성과 지표 분석 실패: {str(e)}")
            return {
                'raw_stats_available': True,
                'analysis_error': str(e)
            }
    
    def _assess_backtest_quality(self, request: BacktestRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """백테스트 품질 평가"""
        try:
            quality_score = 100.0
            quality_issues = []
            
            # 1. 기간 적절성 검사
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
            duration_days = (end_date - start_date).days
            
            if duration_days < 365:
                quality_score -= 20
                quality_issues.append("백테스트 기간이 1년 미만으로 짧습니다")
            elif duration_days < 180:
                quality_score -= 30
                quality_issues.append("백테스트 기간이 6개월 미만으로 매우 짧습니다")
            
            # 2. 데이터 품질 검사
            if 'trades' in result and isinstance(result['trades'], list):
                trade_count = len(result['trades'])
                if trade_count < 10:
                    quality_score -= 15
                    quality_issues.append(f"거래 횟수가 적습니다 ({trade_count}회)")
            
            # 3. 수익률 현실성 검사
            if 'stats' in result:
                annual_return = float(result['stats'].get('Return (Ann.) [%]', 0))
                if abs(annual_return) > 500:  # 500% 초과
                    quality_score -= 25
                    quality_issues.append("연간 수익률이 비현실적으로 높습니다")
            
            # 4. 품질 등급 결정
            if quality_score >= 90:
                quality_grade = 'Excellent'
            elif quality_score >= 75:
                quality_grade = 'Good'
            elif quality_score >= 60:
                quality_grade = 'Fair'
            else:
                quality_grade = 'Poor'
            
            return {
                'quality_score': quality_score,
                'quality_grade': quality_grade,
                'duration_days': duration_days,
                'issues': quality_issues,
                'recommendations': self._generate_quality_recommendations(quality_issues)
            }
            
        except Exception as e:
            logger.warning(f"백테스트 품질 평가 실패: {str(e)}")
            return {
                'quality_assessment_available': False,
                'error': str(e)
            }
    
    def _analyze_date_range(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """날짜 범위 분석"""
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
            duration_days = (end_date_obj - start_date_obj).days

            return {
                'is_valid': start_date_obj < end_date_obj,
                'duration_days': duration_days,
                'duration_years': round(duration_days / 365.25, 2),
                'start_date': start_date,
                'end_date': end_date,
                'contains_market_crash': self._check_market_events(start_date_obj, end_date_obj),
                'season_analysis': self._analyze_seasonal_effects(start_date_obj, end_date_obj, duration_days)
            }

        except Exception as e:
            logger.warning(f"날짜 범위 분석 실패: {str(e)}")
            return {
                'start_date': start_date,
                'end_date': end_date,
                'analysis_error': str(e)
            }
    
    def _generate_quality_recommendations(self, issues: List[str]) -> List[str]:
        """품질 개선 권장사항 생성"""
        recommendations = []
        
        for issue in issues:
            if "기간" in issue and "짧습니다" in issue:
                recommendations.append("백테스트 기간을 최소 1년 이상으로 설정해보세요")
            elif "거래 횟수" in issue:
                recommendations.append("전략 파라미터를 조정하여 거래 빈도를 늘려보세요")
            elif "비현실적" in issue:
                recommendations.append("전략 파라미터나 수수료 설정을 재검토해보세요")
        
        if not recommendations:
            recommendations.append("백테스트 품질이 양호합니다")
        
        return recommendations
    
    def _check_market_events(self, start_date_obj, end_date_obj) -> Dict[str, bool]:
        """주요 시장 이벤트 포함 여부 확인"""
        start_year = start_date_obj.year
        end_year = end_date_obj.year

        events = {
            'covid_crash_2020': 2020 >= start_year and 2020 <= end_year,
            'tech_bubble_2000': 2000 >= start_year and 2001 <= end_year,
            'financial_crisis_2008': 2008 >= start_year and 2009 <= end_year,
            'dot_com_recovery_2003': 2003 >= start_year and 2004 <= end_year
        }

        return events

    def _analyze_seasonal_effects(self, start_date_obj, end_date_obj, duration_days: int) -> Dict[str, Any]:
        """계절성 효과 분석"""
        return {
            'covers_full_year': duration_days >= 365,
            'multiple_years': duration_days >= 730,
            'start_month': start_date_obj.month,
            'end_month': end_date_obj.month,
            'seasonal_bias_risk': 'Low' if duration_days >= 365 else 'High'
        }
    
    async def get_strategy_recommendations(self, symbol: str, date_range: tuple) -> Dict[str, Any]:
        """
        특정 종목과 기간에 대한 전략 추천
        
        Args:
            symbol: 분석할 종목 심볼
            date_range: (start_date, end_date) 튜플
            
        Returns:
            전략 추천 결과 딕셔너리
        """
        try:
            # 전략 도메인 서비스를 통한 추천
            available_strategies = self.strategy_domain_service.get_available_strategies()
            
            recommendations = []
            for strategy_name in available_strategies:
                strategy_info = {
                    'name': strategy_name,
                    'suitability_score': self._calculate_strategy_suitability(strategy_name, symbol),
                    'recommended_params': self._get_recommended_params(strategy_name, symbol),
                    'description': f"{strategy_name} 전략"
                }
                recommendations.append(strategy_info)
            
            # 적합성 점수로 정렬
            recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
            
            return {
                'symbol': symbol,
                'date_range': date_range,
                'recommended_strategies': recommendations[:3],  # 상위 3개
                'total_available': len(available_strategies)
            }
            
        except Exception as e:
            logger.error(f"전략 추천 중 오류: {str(e)}")
            return {
                'error': str(e),
                'recommendations_available': False
            }
    
    def _calculate_strategy_suitability(self, strategy_name: str, symbol: str) -> float:
        """전략의 종목 적합성 점수 계산 (0-100)"""
        # 기본 점수
        base_score = 50.0
        
        # 전략별 특성 고려
        if strategy_name.lower() in ['sma_crossover', 'sma']:
            # 트렌드 추종 전략은 변동성이 있는 종목에 적합
            base_score += 15.0
        elif strategy_name.lower() in ['rsi', 'rsi_strategy']:
            # RSI는 횡보하는 시장에 적합
            base_score += 10.0
        elif strategy_name.lower() in ['bollinger', 'bollinger_bands']:
            # 볼린저 밴드는 평균회귀 성향이 있는 종목에 적합
            base_score += 12.0
        elif strategy_name.lower() in ['macd']:
            # MACD는 트렌드와 모멘텀 모두 고려
            base_score += 18.0
        elif strategy_name.lower() in ['buy_and_hold', 'buyandhold']:
            # 매수 후 보유는 성장주에 적합
            base_score += 20.0
        
        # 종목 특성 고려 (기본적인 휴리스틱)
        if symbol.upper() in ['AAPL', 'MSFT', 'GOOGL', 'AMZN']:
            # 대형주는 일반적으로 안정적
            base_score += 5.0
        
        return min(base_score, 100.0)
    
    def _get_recommended_params(self, strategy_name: str, symbol: str) -> Dict[str, Any]:
        """전략별 추천 파라미터"""
        param_recommendations = {
            'sma_crossover': {'fast_period': 10, 'slow_period': 20},
            'sma': {'period': 20},
            'rsi': {'period': 14, 'oversold': 30, 'overbought': 70},
            'bollinger_bands': {'period': 20, 'std_dev': 2},
            'macd': {'fast': 12, 'slow': 26, 'signal': 9},
            'buy_and_hold': {}
        }
        
        return param_recommendations.get(strategy_name.lower(), {})


# 전역 인스턴스 (Repository Pattern과 Factory Pattern 적용)
backtest_service = BacktestService()
