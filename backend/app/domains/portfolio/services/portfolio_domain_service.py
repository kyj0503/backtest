"""
Portfolio domain - PortfolioDomainService

포트폴리오 관리를 담당하는 도메인 서비스입니다.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import date

from ..entities import PortfolioEntity, AssetEntity
from ..entities.asset import AssetType  # AssetType import 추가
from ..value_objects import Weight, Allocation
from ...data import MarketDataEntity, Price, TickerInfo


class PortfolioDomainService:
    """
    포트폴리오 도메인의 핵심 비즈니스 로직을 담당하는 서비스
    
    책임:
    - 포트폴리오 생성 및 검증
    - 리밸런싱 로직
    - 포트폴리오 분석
    - 자산 배분 최적화
    """
    
    def _map_asset_type(self, data_asset_type) -> AssetType:
        """데이터 도메인의 AssetType을 포트폴리오 도메인의 AssetType으로 매핑"""
        mapping = {
            "stock": AssetType.STOCK,
            "cash": AssetType.CASH,
            "etf": AssetType.ETF,
            "index": AssetType.STOCK,  # index는 stock으로 매핑
        }
        asset_type_value = data_asset_type.value if hasattr(data_asset_type, 'value') else str(data_asset_type)
        return mapping.get(asset_type_value, AssetType.STOCK)
    
    def create_portfolio_from_weights(self,
                                    name: str,
                                    asset_weights: Dict[TickerInfo, float]) -> PortfolioEntity:
        """가중치 딕셔너리로부터 포트폴리오 생성"""
        assets = []
        
        for ticker, weight_value in asset_weights.items():
            weight = Weight(Decimal(str(weight_value)))
            
            # AssetEntity 생성 (필드명에 맞게 수정)
            asset = AssetEntity(
                symbol=str(ticker.symbol),
                name=ticker.company_name or str(ticker.symbol),
                asset_type=self._map_asset_type(ticker.symbol.asset_type),
                target_weight=weight
            )
            assets.append(asset)
        
        return PortfolioEntity(name=name, assets=assets)
    
    def validate_portfolio_weights(self, portfolio: PortfolioEntity) -> List[str]:
        """포트폴리오 가중치 유효성 검증"""
        errors = []
        
        # 총 가중치 계산
        total_weight = sum(asset.target_weight.value for asset in portfolio.assets)
        
        if abs(total_weight - Decimal("1.0")) > Decimal("0.01"):  # 1% 허용 오차
            errors.append(f"Total weight {total_weight:.3f} does not equal 1.0")
        
        # 개별 가중치 검증
        for asset in portfolio.assets:
            if asset.target_weight.value < 0:
                errors.append(f"Negative weight for {asset.symbol}: {asset.target_weight}")
            if asset.target_weight.value > 1:
                errors.append(f"Weight exceeds 100% for {asset.symbol}: {asset.target_weight}")
        
        # 중복 자산 검증
        symbols = [asset.symbol for asset in portfolio.assets]
        duplicates = set([s for s in symbols if symbols.count(s) > 1])
        if duplicates:
            errors.append(f"Duplicate assets found: {duplicates}")
        
        return errors
    
    def calculate_portfolio_allocation(self,
                                     portfolio: PortfolioEntity,
                                     market_data: Dict[str, MarketDataEntity],
                                     total_value: Decimal) -> Allocation:
        """현재 시장 가격 기준으로 포트폴리오 배분 계산"""
        allocations = {}
        
        for asset in portfolio.assets:
            symbol = asset.symbol
            
            # 현금 자산 여부 확인 (asset_type 기준)
            if asset.asset_type.value == "cash":
                # 현금 자산은 1:1 배분
                allocations[symbol] = asset.target_weight.value * total_value
            else:
                # 주식 자산은 현재 가격 기준 계산
                if symbol in market_data:
                    latest_price = market_data[symbol].get_latest_price()
                    if latest_price:
                        target_value = asset.target_weight.value * total_value
                        shares = target_value / latest_price.value
                        allocations[symbol] = shares * latest_price.value
                    else:
                        allocations[symbol] = Decimal("0")
                else:
                    allocations[symbol] = Decimal("0")
        
        return Allocation(allocations)
    
    def calculate_rebalancing_trades(self,
                                   portfolio: PortfolioEntity,
                                   current_values: Dict[str, Decimal],
                                   target_total_value: Decimal) -> Dict[str, Decimal]:
        """
        리밸런싱을 위한 거래량 계산
        
        반환값: 심볼별 거래 금액 (양수: 매수, 음수: 매도)
        """
        trades = {}
        
        for asset in portfolio.assets:
            symbol = asset.symbol
            current_value = current_values.get(symbol, Decimal("0"))
            target_value = asset.target_weight.value * target_total_value
            
            trade_amount = target_value - current_value
            trades[symbol] = trade_amount
        
        return trades
    
    def optimize_portfolio_weights(self,
                                 tickers: List[TickerInfo],
                                 market_data: Dict[str, MarketDataEntity],
                                 start_date: date,
                                 end_date: date,
                                 risk_tolerance: float = 0.5) -> Dict[TickerInfo, float]:
        """
        간단한 포트폴리오 가중치 최적화
        (실제 구현에서는 더 정교한 최적화 알고리즘 사용)
        """
        if not tickers:
            return {}
        
        # 현금 자산과 주식 자산 분리
        cash_assets = [t for t in tickers if t.symbol.is_cash()]
        stock_assets = [t for t in tickers if not t.symbol.is_cash()]
        
        weights = {}
        
        # 현금 자산 가중치 (위험 회피 성향에 따라)
        cash_weight = (1.0 - risk_tolerance) * 0.3  # 최대 30%
        
        if cash_assets:
            for cash_asset in cash_assets:
                weights[cash_asset] = cash_weight / len(cash_assets)
        
        # 주식 자산 가중치 (균등 분배 + 변동성 조정)
        remaining_weight = 1.0 - cash_weight
        
        if stock_assets:
            # 변동성 계산
            volatilities = {}
            for ticker in stock_assets:
                symbol = str(ticker.symbol)
                if symbol in market_data:
                    entity = market_data[symbol]
                    vol = entity.calculate_volatility(start_date, end_date)
                    volatilities[ticker] = vol if vol else 0.1  # 기본 변동성
                else:
                    volatilities[ticker] = 0.1
            
            # 역변동성 가중 (변동성이 낮을수록 높은 가중치)
            inv_vol_sum = sum(1.0 / vol for vol in volatilities.values())
            
            for ticker in stock_assets:
                inv_vol_weight = (1.0 / volatilities[ticker]) / inv_vol_sum
                weights[ticker] = remaining_weight * inv_vol_weight
        
        return weights
    
    def calculate_portfolio_metrics(self,
                                  portfolio: PortfolioEntity,
                                  market_data: Dict[str, MarketDataEntity],
                                  start_date: date,
                                  end_date: date) -> Dict[str, float]:
        """포트폴리오 성과 지표 계산"""
        metrics = {}
        
        # 자산별 수익률 계산
        asset_returns = {}
        for asset in portfolio.assets:
            symbol = asset.symbol
            
            # 현금 자산 여부 확인
            if asset.asset_type.value == "cash":
                # 현금 자산은 0% 수익률
                asset_returns[symbol] = 0.0
            elif symbol in market_data:
                entity = market_data[symbol]
                price_series = entity.get_price_series(start_date, end_date)
                
                if len(price_series) >= 2:
                    start_price = price_series[0][1]
                    end_price = price_series[-1][1]
                    
                    if start_price.value > 0:
                        total_return = float(end_price.percentage_change(start_price))
                        asset_returns[symbol] = total_return
                    else:
                        asset_returns[symbol] = 0.0
                else:
                    asset_returns[symbol] = 0.0
            else:
                asset_returns[symbol] = 0.0
        
        # 포트폴리오 전체 수익률 (가중 평균)
        portfolio_return = 0.0
        for asset in portfolio.assets:
            symbol = asset.symbol
            weight = float(asset.target_weight.value)
            asset_return = asset_returns.get(symbol, 0.0)
            portfolio_return += weight * asset_return
        
        metrics["total_return"] = portfolio_return
        
        # 포트폴리오 변동성 계산 (단순화된 버전)
        weighted_volatility = 0.0
        for asset in portfolio.assets:
            symbol = asset.symbol
            weight = float(asset.target_weight.value)
            
            if symbol in market_data and asset.asset_type.value != "cash":
                entity = market_data[symbol]
                vol = entity.calculate_volatility(start_date, end_date)
                if vol:
                    weighted_volatility += weight * vol
        
        metrics["volatility"] = weighted_volatility
        
        # 샤프 비율 (무위험 수익률 0으로 가정)
        if weighted_volatility > 0:
            metrics["sharpe_ratio"] = portfolio_return / weighted_volatility
        else:
            metrics["sharpe_ratio"] = 0.0
        
        # 다변화 점수 (자산 개수 기준 단순 계산)
        num_assets = len([a for a in portfolio.assets if a.asset_type.value != "cash"])
        if num_assets > 1:
            metrics["diversification_score"] = min(1.0, num_assets / 10.0)  # 10개 자산일 때 1.0
        else:
            metrics["diversification_score"] = 0.0
        
        return metrics
    
    def suggest_rebalancing_frequency(self, portfolio: PortfolioEntity) -> str:
        """포트폴리오 특성에 따른 리밸런싱 주기 제안"""
        num_assets = len(portfolio.assets)
        has_cash = any(asset.asset_type.value == "cash" for asset in portfolio.assets)
        
        if num_assets <= 2 and has_cash:
            return "monthly"  # 단순한 포트폴리오는 월간 리밸런싱
        elif num_assets <= 5:
            return "quarterly"  # 중간 규모는 분기별
        else:
            return "semiannually"  # 복잡한 포트폴리오는 반기별
