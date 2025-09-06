"""
도메인 서비스가 통합된 향상된 포트폴리오 서비스 (Phase 4)

기존 PortfolioService와 완전 호환되며, DDD 도메인 서비스의 고급 기능을 추가로 제공합니다.
"""
import logging
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
import pandas as pd
import numpy as np

from app.services.portfolio_service import PortfolioService, PortfolioBacktestService
from app.domains.portfolio.services.portfolio_domain_service import PortfolioDomainService
from app.domains.data.services.data_domain_service import DataDomainService
from app.domains.data.value_objects.ticker_info import TickerInfo
from app.domains.portfolio.value_objects.weight import Weight
from app.domains.portfolio.value_objects.allocation import Allocation
from app.domains.portfolio.entities.portfolio_entity import PortfolioEntity
from app.domains.data.entities.market_data_entity import MarketDataEntity
from app.models.schemas import PortfolioBacktestRequest, PortfolioStock

logger = logging.getLogger(__name__)


class EnhancedPortfolioService(PortfolioService):
    """
    도메인 서비스가 통합된 향상된 포트폴리오 서비스
    
    기존 PortfolioService의 모든 기능을 유지하면서,
    DDD 도메인 서비스의 고급 포트폴리오 관리 기능을 추가로 제공합니다.
    """
    
    def __init__(self):
        """Enhanced 포트폴리오 서비스 초기화"""
        super().__init__()
        
        # DDD 도메인 서비스 초기화
        self.portfolio_domain_service = PortfolioDomainService()
        self.data_domain_service = DataDomainService()
        
        logger.info("Enhanced 포트폴리오 서비스가 도메인 서비스와 함께 초기화되었습니다")
    
    async def run_portfolio_backtest_with_optimization(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """
        포트폴리오 최적화가 포함된 백테스트 실행
        
        기존 포트폴리오 백테스트에 다음과 같은 고급 분석을 추가합니다:
        - 포트폴리오 가중치 최적화
        - 자산 간 상관관계 분석
        - 다변화 효과 분석
        - 리밸런싱 추천
        """
        try:
            # 1. 기존 포트폴리오 백테스트 실행
            base_result = await self.run_portfolio_backtest(request)
            
            # 2. 도메인 서비스를 활용한 고급 분석 추가
            enhanced_result = await self._enhance_portfolio_result(request, base_result)
            
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Enhanced 포트폴리오 백테스트 실행 중 오류: {str(e)}")
            raise
    
    async def _enhance_portfolio_result(self, request: PortfolioBacktestRequest, base_result: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 백테스트 결과에 도메인 분석 추가"""
        
        # 기본 결과 복사
        enhanced_result = base_result.copy()
        
        # 도메인 분석 결과 추가
        portfolio_analysis = {}
        
        try:
            # 1. 포트폴리오 최적화 분석
            optimization_analysis = await self._analyze_portfolio_optimization(request)
            portfolio_analysis['optimization'] = optimization_analysis
            
            # 2. 상관관계 분석
            correlation_analysis = await self._analyze_asset_correlation(request)
            portfolio_analysis['correlation'] = correlation_analysis
            
            # 3. 다변화 분석
            diversification_analysis = self._analyze_diversification(request)
            portfolio_analysis['diversification'] = diversification_analysis
            
            # 4. 리밸런싱 추천
            rebalancing_recommendations = self._generate_rebalancing_recommendations(request)
            portfolio_analysis['rebalancing'] = rebalancing_recommendations
            
            # 5. 포트폴리오 품질 평가
            quality_assessment = self._assess_portfolio_quality(request, base_result)
            portfolio_analysis['quality'] = quality_assessment
            
            # 도메인 분석 결과를 기본 결과에 추가
            enhanced_result['portfolio_analysis'] = portfolio_analysis
            
        except Exception as e:
            logger.warning(f"포트폴리오 도메인 분석 중 오류 발생 (기본 결과는 유지): {str(e)}")
            enhanced_result['portfolio_analysis'] = {
                'error': f"포트폴리오 분석 중 오류: {str(e)}",
                'base_result_available': True
            }
        
        return enhanced_result
    
    async def _analyze_portfolio_optimization(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """포트폴리오 최적화 분석"""
        try:
            # 요청에서 티커 정보 추출
            tickers = []
            current_weights = {}
            
            for stock in request.stocks:
                if stock.symbol.upper() == 'CASH':
                    ticker = TickerInfo.cash_asset('USD')
                else:
                    ticker = TickerInfo.us_stock(stock.symbol, stock.symbol, 'Unknown')
                
                tickers.append(ticker)
                current_weights[ticker] = stock.weight / 100.0  # 백분율을 비율로 변환
            
            # 날짜 범위 설정
            start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
            
            # 모의 시장 데이터 생성 (실제 구현에서는 실제 데이터 사용)
            market_data_dict = {}
            for ticker in tickers:
                if ticker.asset_type.value == 'cash':
                    market_data = self.data_domain_service.generate_cash_data_series(
                        ticker, start_date, end_date
                    )
                else:
                    # 실제 구현에서는 yfinance 데이터를 사용
                    market_data = self._create_mock_stock_data(ticker, start_date, end_date)
                
                market_data_dict[ticker.symbol] = market_data
            
            # 포트폴리오 최적화 실행
            optimized_weights = self.portfolio_domain_service.optimize_portfolio_weights(
                tickers, market_data_dict, start_date, end_date, risk_tolerance=0.6
            )
            
            # 결과 분석
            current_allocation = Allocation({
                ticker.symbol: Weight(Decimal(str(weight))) 
                for ticker, weight in current_weights.items()
            })
            
            optimized_allocation = Allocation({
                symbol: Weight(Decimal(str(weight))) 
                for symbol, weight in optimized_weights.items()
            })
            
            return {
                'current_weights': {ticker.symbol: weight for ticker, weight in current_weights.items()},
                'optimized_weights': optimized_weights,
                'current_diversification': current_allocation.calculate_diversification_score(),
                'optimized_diversification': optimized_allocation.calculate_diversification_score(),
                'improvement_potential': self._calculate_improvement_potential(current_weights, optimized_weights),
                'optimization_recommendation': self._generate_optimization_recommendation(current_weights, optimized_weights)
            }
            
        except Exception as e:
            logger.warning(f"포트폴리오 최적화 분석 실패: {str(e)}")
            return {
                'optimization_available': False,
                'error': str(e)
            }
    
    async def _analyze_asset_correlation(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """자산 간 상관관계 분석"""
        try:
            # 요청에서 자산 정보 추출
            entities = []
            asset_names = []
            
            for stock in request.stocks:
                if stock.symbol.upper() == 'CASH':
                    ticker = TickerInfo.cash_asset('USD')
                    # 현금 자산 데이터 생성
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
                    entity = self.data_domain_service.generate_cash_data_series(ticker, start_date, end_date)
                else:
                    ticker = TickerInfo.us_stock(stock.symbol, stock.symbol, 'Unknown')
                    # 모의 주식 데이터 생성
                    start_date = datetime.strptime(request.start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(request.end_date, '%Y-%m-%d').date()
                    entity = self._create_mock_stock_data(ticker, start_date, end_date)
                
                entities.append(entity)
                asset_names.append(stock.symbol)
            
            # 상관관계 매트릭스 계산
            correlation_matrix = self.data_domain_service.calculate_correlation_matrix(entities)
            
            # 상관관계 분석 결과
            analysis = {
                'correlation_matrix': {},
                'high_correlation_pairs': [],
                'low_correlation_pairs': [],
                'diversification_effectiveness': 'Good'
            }
            
            # 상관관계 매트릭스 정리
            for (asset1, asset2), correlation in correlation_matrix.items():
                pair_key = f"{asset1}_vs_{asset2}"
                analysis['correlation_matrix'][pair_key] = round(correlation, 3)
                
                # 높은 상관관계 (0.7 이상)
                if abs(correlation) >= 0.7 and asset1 != asset2:
                    analysis['high_correlation_pairs'].append({
                        'assets': f"{asset1} vs {asset2}",
                        'correlation': round(correlation, 3),
                        'warning': "높은 상관관계로 인한 분산 효과 제한"
                    })
                
                # 낮은 상관관계 (0.3 이하)
                elif abs(correlation) <= 0.3 and asset1 != asset2:
                    analysis['low_correlation_pairs'].append({
                        'assets': f"{asset1} vs {asset2}",
                        'correlation': round(correlation, 3),
                        'benefit': "낮은 상관관계로 인한 우수한 분산 효과"
                    })
            
            # 전체적인 분산 효과 평가
            if len(analysis['high_correlation_pairs']) > len(entities) / 2:
                analysis['diversification_effectiveness'] = 'Poor'
            elif len(analysis['low_correlation_pairs']) > len(entities) / 2:
                analysis['diversification_effectiveness'] = 'Excellent'
            
            return analysis
            
        except Exception as e:
            logger.warning(f"상관관계 분석 실패: {str(e)}")
            return {
                'correlation_analysis_available': False,
                'error': str(e)
            }
    
    def _analyze_diversification(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """다변화 분석"""
        try:
            # 가중치 딕셔너리 생성
            weights_dict = {}
            for stock in request.stocks:
                weights_dict[stock.symbol] = Weight(Decimal(str(stock.weight / 100.0)))
            
            # Allocation 값 객체 생성
            allocation = Allocation(weights_dict)
            
            # 다변화 분석
            diversification_score = allocation.calculate_diversification_score()
            is_well_diversified = allocation.is_well_diversified()
            
            # 분석 결과
            analysis = {
                'diversification_score': round(diversification_score, 3),
                'is_well_diversified': is_well_diversified,
                'asset_count': len(weights_dict),
                'largest_weight': max(weight.value for weight in weights_dict.values()),
                'smallest_weight': min(weight.value for weight in weights_dict.values()),
                'concentration_risk': self._assess_concentration_risk(weights_dict),
                'recommendations': self._generate_diversification_recommendations(allocation)
            }
            
            return analysis
            
        except Exception as e:
            logger.warning(f"다변화 분석 실패: {str(e)}")
            return {
                'diversification_analysis_available': False,
                'error': str(e)
            }
    
    def _generate_rebalancing_recommendations(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """리밸런싱 추천 생성"""
        try:
            total_value = request.total_investment
            current_weights = {stock.symbol: stock.weight / 100.0 for stock in request.stocks}
            
            recommendations = {
                'frequency': self._recommend_rebalancing_frequency(current_weights),
                'threshold': self._recommend_rebalancing_threshold(current_weights),
                'cost_analysis': self._analyze_rebalancing_costs(request),
                'calendar_recommendation': self._recommend_rebalancing_calendar(),
                'tax_considerations': self._analyze_tax_implications()
            }
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"리밸런싱 추천 생성 실패: {str(e)}")
            return {
                'rebalancing_recommendations_available': False,
                'error': str(e)
            }
    
    def _assess_portfolio_quality(self, request: PortfolioBacktestRequest, result: Dict[str, Any]) -> Dict[str, Any]:
        """포트폴리오 품질 평가"""
        try:
            quality_score = 100.0
            quality_issues = []
            
            # 1. 자산 개수 평가
            asset_count = len(request.stocks)
            if asset_count < 3:
                quality_score -= 20
                quality_issues.append("자산 개수가 부족합니다 (최소 3개 권장)")
            elif asset_count > 20:
                quality_score -= 10
                quality_issues.append("자산 개수가 과도합니다 (관리 복잡성 증가)")
            
            # 2. 가중치 분산 평가
            weights = [stock.weight for stock in request.stocks]
            max_weight = max(weights)
            if max_weight > 50:
                quality_score -= 15
                quality_issues.append(f"단일 자산 비중이 과도합니다 ({max_weight}%)")
            
            # 3. 현금 비중 평가
            cash_weight = sum(stock.weight for stock in request.stocks if stock.symbol.upper() == 'CASH')
            if cash_weight > 30:
                quality_score -= 10
                quality_issues.append(f"현금 비중이 높습니다 ({cash_weight}%)")
            elif cash_weight < 5:
                quality_score -= 5
                quality_issues.append("현금 비중이 낮아 유동성이 부족할 수 있습니다")
            
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
                'asset_count': asset_count,
                'max_single_weight': max_weight,
                'cash_weight': cash_weight,
                'issues': quality_issues,
                'recommendations': self._generate_portfolio_recommendations(quality_issues)
            }
            
        except Exception as e:
            logger.warning(f"포트폴리오 품질 평가 실패: {str(e)}")
            return {
                'quality_assessment_available': False,
                'error': str(e)
            }
    
    def _create_mock_stock_data(self, ticker: TickerInfo, start_date: date, end_date: date) -> MarketDataEntity:
        """모의 주식 데이터 생성 (테스트용)"""
        entity = self.data_domain_service.create_market_data_entity(ticker)
        
        # 간단한 모의 데이터 생성
        current_date = start_date
        base_price = 100.0
        
        while current_date <= end_date:
            # 간단한 랜덤 워크
            price_change = np.random.normal(0, 0.02)  # 2% 변동성
            base_price *= (1 + price_change)
            
            data_point = self.data_domain_service.create_stock_data_point(
                ticker, current_date, base_price, base_price * 1.01, base_price * 0.99, base_price, 1000000
            )
            entity.add_data_point(data_point)
            
            current_date = date.fromordinal(current_date.toordinal() + 1)
        
        return entity
    
    def _calculate_improvement_potential(self, current_weights: Dict[str, float], optimized_weights: Dict[str, float]) -> Dict[str, Any]:
        """개선 잠재력 계산"""
        total_change = sum(abs(optimized_weights.get(symbol, 0) - weight) 
                          for symbol, weight in current_weights.items())
        
        return {
            'total_weight_change': round(total_change, 3),
            'significant_changes': total_change > 0.1,
            'improvement_level': 'High' if total_change > 0.2 else 'Medium' if total_change > 0.1 else 'Low'
        }
    
    def _generate_optimization_recommendation(self, current_weights: Dict[str, float], optimized_weights: Dict[str, float]) -> str:
        """최적화 추천 메시지 생성"""
        total_change = sum(abs(optimized_weights.get(symbol, 0) - weight) 
                          for symbol, weight in current_weights.items())
        
        if total_change > 0.2:
            return "현재 포트폴리오를 크게 조정하면 리스크 대비 수익률을 개선할 수 있습니다"
        elif total_change > 0.1:
            return "일부 자산의 비중을 조정하면 포트폴리오 효율성을 높일 수 있습니다"
        else:
            return "현재 포트폴리오가 이미 잘 최적화되어 있습니다"
    
    def _assess_concentration_risk(self, weights_dict: Dict[str, Weight]) -> str:
        """집중도 리스크 평가"""
        max_weight = max(weight.value for weight in weights_dict.values())
        
        if max_weight > 0.5:
            return 'High'
        elif max_weight > 0.3:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_diversification_recommendations(self, allocation: Allocation) -> List[str]:
        """다변화 개선 권장사항"""
        recommendations = []
        
        if not allocation.is_well_diversified():
            recommendations.append("자산 간 비중을 더 균등하게 배분해보세요")
            recommendations.append("새로운 자산군 추가를 고려해보세요")
        
        if allocation.calculate_diversification_score() < 0.5:
            recommendations.append("포트폴리오 집중도가 높습니다. 분산투자를 늘려보세요")
        
        if not recommendations:
            recommendations.append("다변화가 잘 이루어진 포트폴리오입니다")
        
        return recommendations
    
    def _recommend_rebalancing_frequency(self, weights: Dict[str, float]) -> str:
        """리밸런싱 빈도 추천"""
        volatility_estimate = np.std(list(weights.values()))
        
        if volatility_estimate > 0.3:
            return "분기별 (3개월)"
        elif volatility_estimate > 0.2:
            return "반기별 (6개월)"
        else:
            return "연간 (12개월)"
    
    def _recommend_rebalancing_threshold(self, weights: Dict[str, float]) -> str:
        """리밸런싱 임계값 추천"""
        return "목표 비중에서 ±5% 이상 벗어날 때"
    
    def _analyze_rebalancing_costs(self, request: PortfolioBacktestRequest) -> Dict[str, Any]:
        """리밸런싱 비용 분석"""
        commission = getattr(request, 'commission', 0.002)
        total_value = request.total_investment
        
        estimated_cost = total_value * commission * 0.5  # 평균적으로 50%의 자산이 거래된다고 가정
        
        return {
            'estimated_cost_per_rebalancing': round(estimated_cost, 2),
            'annual_cost_estimate': round(estimated_cost * 4, 2),  # 분기별 리밸런싱 가정
            'cost_percentage': round((estimated_cost / total_value) * 100, 3)
        }
    
    def _recommend_rebalancing_calendar(self) -> List[str]:
        """리밸런싱 일정 추천"""
        return [
            "매년 1월: 신년 포트폴리오 점검",
            "매년 7월: 중간 점검 및 조정",
            "분기별 말일: 목표 비중 확인",
            "시장 급변동 시: 임시 리밸런싱 검토"
        ]
    
    def _analyze_tax_implications(self) -> List[str]:
        """세금 영향 분석"""
        return [
            "장기 보유 자산의 경우 세금 혜택 고려",
            "손실 실현을 통한 세금 절약 기회 검토",
            "연말 세금 계획에 맞춘 리밸런싱 타이밍 조정",
            "배당 지급 시기를 고려한 매매 타이밍"
        ]
    
    def _generate_portfolio_recommendations(self, issues: List[str]) -> List[str]:
        """포트폴리오 개선 권장사항"""
        recommendations = []
        
        for issue in issues:
            if "자산 개수" in issue and "부족" in issue:
                recommendations.append("다양한 섹터의 주식이나 ETF를 추가해보세요")
            elif "과도합니다" in issue and "비중" in issue:
                recommendations.append("주요 종목의 비중을 줄이고 다른 자산에 분산해보세요")
            elif "현금 비중" in issue:
                if "높습니다" in issue:
                    recommendations.append("현금 일부를 투자 자산으로 전환해보세요")
                else:
                    recommendations.append("비상 자금을 위한 현금 비중을 늘려보세요")
        
        if not recommendations:
            recommendations.append("포트폴리오 구성이 양호합니다")
        
        return recommendations
    
    async def optimize_portfolio_weights(self, stocks: List[Dict[str, Any]], risk_tolerance: float = 0.6) -> Dict[str, float]:
        """
        포트폴리오 가중치 최적화
        
        Args:
            stocks: 주식 정보 리스트 [{'symbol': 'AAPL', 'weight': 60}, ...]
            risk_tolerance: 리스크 허용도 (0.0 ~ 1.0)
            
        Returns:
            최적화된 가중치 딕셔너리
        """
        try:
            # 티커 정보 생성
            tickers = []
            for stock in stocks:
                if stock['symbol'].upper() == 'CASH':
                    ticker = TickerInfo.cash_asset('USD')
                else:
                    ticker = TickerInfo.us_stock(stock['symbol'], stock['symbol'], 'Unknown')
                tickers.append(ticker)
            
            # 모의 시장 데이터 생성 (실제 구현에서는 실제 데이터 사용)
            start_date = date(2023, 1, 1)
            end_date = date(2024, 1, 1)
            market_data_dict = {}
            
            for ticker in tickers:
                if ticker.asset_type.value == 'cash':
                    market_data = self.data_domain_service.generate_cash_data_series(
                        ticker, start_date, end_date
                    )
                else:
                    market_data = self._create_mock_stock_data(ticker, start_date, end_date)
                
                market_data_dict[ticker.symbol] = market_data
            
            # 포트폴리오 최적화 실행
            optimized_weights = self.portfolio_domain_service.optimize_portfolio_weights(
                tickers, market_data_dict, start_date, end_date, risk_tolerance
            )
            
            return optimized_weights
            
        except Exception as e:
            logger.error(f"포트폴리오 가중치 최적화 중 오류: {str(e)}")
            # 실패 시 균등 가중치 반환
            equal_weight = 1.0 / len(stocks)
            return {stock['symbol']: equal_weight for stock in stocks}


# 전역 인스턴스 생성 (기존 패턴 유지)
enhanced_portfolio_service = EnhancedPortfolioService()
