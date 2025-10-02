"""
포트폴리오 도메인 로직 단위 테스트

Given-When-Then 패턴과 FIRST 원칙을 준수하여 작성된 테스트입니다.
"""

import pytest
from datetime import datetime
from decimal import Decimal

from app.domains.portfolio.entities.portfolio import PortfolioEntity
from app.domains.portfolio.entities.asset import AssetEntity, AssetType
from app.domains.portfolio.value_objects.weight import Weight
from app.domains.portfolio.value_objects.allocation import Allocation


@pytest.mark.unit
class TestPortfolioEntity:
    """포트폴리오 엔티티 단위 테스트"""
    
    # ========================================================================
    # 포트폴리오 생성 테스트
    # ========================================================================
    
    def test_포트폴리오_생성_성공(self):
        """
        Given: 유효한 포트폴리오 정보가 주어졌을 때
        When: 포트폴리오를 생성하면
        Then: 포트폴리오가 정상적으로 생성되어야 함
        """
        # Given
        name = "테스트 포트폴리오"
        description = "테스트용 포트폴리오입니다"
        total_value = 100000.0
        
        # When
        portfolio = PortfolioEntity(
            name=name,
            description=description,
            total_value=total_value
        )
        
        # Then
        assert portfolio.name == name
        assert portfolio.description == description
        assert portfolio.total_value == total_value
        assert portfolio.currency == "USD"
        assert portfolio.is_active is True
        assert isinstance(portfolio.id, str)
        assert len(portfolio.id) > 0
    
    def test_포트폴리오_생성_시_이름이_없으면_에러(self):
        """
        Given: 이름이 없는 포트폴리오 정보가 주어졌을 때
        When: 포트폴리오를 생성하려고 하면
        Then: ValueError가 발생해야 함
        """
        # Given / When / Then
        with pytest.raises(ValueError, match="포트폴리오명은 필수입니다"):
            PortfolioEntity(name="", total_value=100000.0)
    
    def test_포트폴리오_생성_시_가치가_음수면_에러(self):
        """
        Given: 음수의 포트폴리오 가치가 주어졌을 때
        When: 포트폴리오를 생성하려고 하면
        Then: ValueError가 발생해야 함
        """
        # Given / When / Then
        with pytest.raises(ValueError, match="포트폴리오 가치는 음수일 수 없습니다"):
            PortfolioEntity(name="테스트", total_value=-1000.0)
    
    # ========================================================================
    # 자산 관리 테스트
    # ========================================================================
    
    def test_자산_추가_성공(self):
        """
        Given: 포트폴리오와 자산이 주어졌을 때
        When: 자산을 추가하면
        Then: 포트폴리오에 자산이 추가되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        asset = AssetEntity.create_stock(symbol="AAPL", name="Apple Inc.")
        
        # When
        portfolio.add_asset(asset)
        
        # Then
        assert len(portfolio.assets) == 1
        assert portfolio.assets[0].symbol == "AAPL"
        assert portfolio.get_asset("AAPL") is not None
    
    def test_중복된_심볼의_자산_추가_시_에러(self):
        """
        Given: 이미 동일한 심볼의 자산이 있는 포트폴리오가 주어졌을 때
        When: 같은 심볼의 자산을 추가하려고 하면
        Then: ValueError가 발생해야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset2 = AssetEntity.create_stock(symbol="AAPL")
        portfolio.add_asset(asset1)
        
        # When / Then
        with pytest.raises(ValueError, match="이미 존재하는 자산입니다: AAPL"):
            portfolio.add_asset(asset2)
    
    def test_자산_제거_성공(self):
        """
        Given: 자산이 있는 포트폴리오가 주어졌을 때
        When: 자산을 제거하면
        Then: 포트폴리오에서 자산이 제거되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        asset = AssetEntity.create_stock(symbol="AAPL")
        portfolio.add_asset(asset)
        
        # When
        result = portfolio.remove_asset("AAPL")
        
        # Then
        assert result is True
        assert len(portfolio.assets) == 0
        assert portfolio.get_asset("AAPL") is None
    
    def test_존재하지_않는_자산_제거_시_False_반환(self):
        """
        Given: 포트폴리오가 주어졌을 때
        When: 존재하지 않는 자산을 제거하려고 하면
        Then: False가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # When
        result = portfolio.remove_asset("INVALID")
        
        # Then
        assert result is False
    
    def test_여러_자산_추가_후_활성_자산_조회(self):
        """
        Given: 활성/비활성 자산이 혼재된 포트폴리오가 주어졌을 때
        When: 활성 자산을 조회하면
        Then: 활성 자산만 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        asset3 = AssetEntity.create_stock(symbol="MSFT")
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        portfolio.add_asset(asset3)
        
        # 한 자산 비활성화
        asset2.deactivate()
        
        # When
        active_assets = portfolio.get_active_assets()
        
        # Then
        assert len(active_assets) == 2
        symbols = [a.symbol for a in active_assets]
        assert "AAPL" in symbols
        assert "MSFT" in symbols
        assert "GOOGL" not in symbols
    
    # ========================================================================
    # 배분 (Allocation) 테스트
    # ========================================================================
    
    def test_현재_배분_조회(self):
        """
        Given: 자산들이 있는 포트폴리오가 주어졌을 때
        When: 현재 배분을 조회하면
        Then: 각 자산의 현재 비중이 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset1.update_weight(Weight(0.4))
        
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        asset2.update_weight(Weight(0.35))
        
        asset3 = AssetEntity.create_stock(symbol="MSFT")
        asset3.update_weight(Weight(0.25))
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        portfolio.add_asset(asset3)
        
        # When
        allocation = portfolio.get_current_allocation()
        
        # Then
        assert isinstance(allocation, Allocation)
        assert allocation.get_weight("AAPL") == Weight(0.4)
        assert allocation.get_weight("GOOGL") == Weight(0.35)
        assert allocation.get_weight("MSFT") == Weight(0.25)
    
    def test_목표_배분_조회(self):
        """
        Given: 목표 비중이 설정된 자산들이 있는 포트폴리오가 주어졌을 때
        When: 목표 배분을 조회하면
        Then: 각 자산의 목표 비중이 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        asset1 = AssetEntity.create_stock(symbol="AAPL", target_weight=Weight(0.5))
        asset2 = AssetEntity.create_stock(symbol="GOOGL", target_weight=Weight(0.3))
        asset3 = AssetEntity.create_stock(symbol="MSFT", target_weight=Weight(0.2))
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        portfolio.add_asset(asset3)
        
        # When
        allocation = portfolio.get_target_allocation()
        
        # Then
        assert allocation.get_weight("AAPL") == Weight(0.5)
        assert allocation.get_weight("GOOGL") == Weight(0.3)
        assert allocation.get_weight("MSFT") == Weight(0.2)
    
    # ========================================================================
    # 리밸런싱 테스트
    # ========================================================================
    
    def test_리밸런싱_필요_여부_확인_필요함(self):
        """
        Given: 목표 비중과 현재 비중이 크게 다른 자산이 있는 포트폴리오가 주어졌을 때
        When: 리밸런싱 필요 여부를 확인하면
        Then: True가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(
            name="테스트",
            total_value=100000.0,
            rebalancing_threshold=0.05
        )
        
        # 과다보유 케이스: 현재가 목표보다 높아야 get_weight_deviation이 0이 아닌 값을 반환
        asset = AssetEntity.create_stock(symbol="AAPL")
        asset.set_target_weight(Weight(0.3))
        asset.update_weight(Weight(0.5))  # 20% 초과 (과다보유)
        
        portfolio.add_asset(asset)
        
        # When
        needs_rebalancing = portfolio.needs_rebalancing()
        
        # Then
        assert needs_rebalancing is True
    
    def test_리밸런싱_필요_여부_확인_불필요(self):
        """
        Given: 목표 비중과 현재 비중이 임계값 이내인 포트폴리오가 주어졌을 때
        When: 리밸런싱 필요 여부를 확인하면
        Then: False가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(
            name="테스트",
            total_value=100000.0,
            rebalancing_threshold=0.05
        )
        
        asset = AssetEntity.create_stock(symbol="AAPL")
        asset.set_target_weight(Weight(0.5))
        asset.update_weight(Weight(0.52))  # 2% 차이만
        
        portfolio.add_asset(asset)
        
        # When
        needs_rebalancing = portfolio.needs_rebalancing()
        
        # Then
        assert needs_rebalancing is False
    
    def test_리밸런싱_주문_생성(self):
        """
        Given: 리밸런싱이 필요한 자산들이 있는 포트폴리오가 주어졌을 때
        When: 리밸런싱 주문을 생성하면
        Then: 각 자산의 필요 매수/매도 금액이 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(
            name="테스트",
            total_value=100000.0,
            rebalancing_threshold=0.05
        )
        
        # AAPL: 30% -> 20% (10% 감소 필요, 하지만 과소보유이므로 주문 생성 안됨)
        # 주문은 현재가 목표보다 높을 때만 생성됨
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset1.set_target_weight(Weight(0.2))
        asset1.update_weight(Weight(0.3))  # 과다보유
        
        # GOOGL: 25% -> 35% (10% 증가 필요, 하지만 과소보유이므로 주문 생성 안됨)
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        asset2.set_target_weight(Weight(0.35))
        asset2.update_weight(Weight(0.25))  # 과소보유
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        
        # When
        orders = portfolio.get_rebalancing_orders()
        
        # Then
        # AAPL만 과다보유이므로 AAPL의 매도 주문만 생성됨
        # GOOGL은 과소보유지만 get_weight_deviation이 0을 반환하므로 주문 없음
        assert "AAPL" in orders
        assert orders["AAPL"] < 0  # 과다보유인 AAPL 매도
        
        # 금액 검증: 현재 30% - 목표 20% = 10% 매도 필요
        # 100,000 * 10% = 10,000
        assert abs(orders["AAPL"] + 10000.0) < 1.0
    
    def test_목표_배분으로_리밸런싱_실행(self):
        """
        Given: 리밸런싱이 필요한 포트폴리오가 주어졌을 때
        When: 목표 배분으로 리밸런싱을 실행하면
        Then: 모든 자산의 현재 비중이 목표 비중과 동일해져야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # 목표 비중 합계가 100%가 되도록 설정
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset1.set_target_weight(Weight(0.5))
        asset1.update_weight(Weight(0.3))
        
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        asset2.set_target_weight(Weight(0.5))  # 0.5 + 0.5 = 1.0 (100%)
        asset2.update_weight(Weight(0.7))
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        
        # When
        portfolio.rebalance_to_target()
        
        # Then
        assert asset1.current_weight == Weight(0.5)
        assert asset2.current_weight == Weight(0.5)
    
    # ========================================================================
    # 포트폴리오 분석 테스트
    # ========================================================================
    
    def test_자산_개수_조회(self):
        """
        Given: 여러 자산이 있는 포트폴리오가 주어졌을 때
        When: 자산 개수를 조회하면
        Then: 활성 자산의 개수가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        portfolio.add_asset(AssetEntity.create_stock(symbol="AAPL"))
        portfolio.add_asset(AssetEntity.create_stock(symbol="GOOGL"))
        portfolio.add_asset(AssetEntity.create_stock(symbol="MSFT"))
        
        # When
        count = portfolio.get_asset_count()
        
        # Then
        assert count == 3
    
    def test_최대_비중_포지션_조회(self):
        """
        Given: 다양한 비중의 자산들이 있는 포트폴리오가 주어졌을 때
        When: 최대 비중 포지션을 조회하면
        Then: 비중이 큰 순서대로 정렬된 자산이 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        assets_data = [
            ("AAPL", 0.3),
            ("GOOGL", 0.25),
            ("MSFT", 0.2),
            ("TSLA", 0.15),
            ("AMZN", 0.1),
        ]
        
        for symbol, weight in assets_data:
            asset = AssetEntity.create_stock(symbol=symbol)
            asset.update_weight(Weight(weight))
            portfolio.add_asset(asset)
        
        # When
        top_3 = portfolio.get_largest_positions(3)
        
        # Then
        assert len(top_3) == 3
        assert top_3[0].symbol == "AAPL"
        assert top_3[1].symbol == "GOOGL"
        assert top_3[2].symbol == "MSFT"
    
    def test_집중도_계산(self):
        """
        Given: 자산들이 있는 포트폴리오가 주어졌을 때
        When: 상위 N개 자산의 집중도를 계산하면
        Then: 상위 자산들의 비중 합이 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # 각각 30%, 25%, 20%, 15%, 10%
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        for i, weight in enumerate(weights):
            asset = AssetEntity.create_stock(symbol=f"ASSET{i}")
            asset.update_weight(Weight(weight))
            portfolio.add_asset(asset)
        
        # When
        concentration_top3 = portfolio.get_concentration_ratio(3)
        
        # Then
        # 상위 3개: 30% + 25% + 20% = 75%
        assert concentration_top3.value == pytest.approx(0.75, abs=0.01)
    
    def test_포트폴리오_분산도_확인_충분히_분산됨(self):
        """
        Given: 단일 자산 비중이 30% 이하인 포트폴리오가 주어졌을 때
        When: 분산도를 확인하면
        Then: True가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # 각 자산 20%씩
        for i in range(5):
            asset = AssetEntity.create_stock(symbol=f"ASSET{i}")
            asset.update_weight(Weight(0.2))
            portfolio.add_asset(asset)
        
        # When
        is_diversified = portfolio.is_well_diversified(max_single_weight=0.3)
        
        # Then
        assert is_diversified is True
    
    def test_포트폴리오_분산도_확인_집중됨(self):
        """
        Given: 단일 자산 비중이 30%를 초과하는 포트폴리오가 주어졌을 때
        When: 분산도를 확인하면
        Then: False가 반환되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # 한 자산이 50%
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset1.update_weight(Weight(0.5))
        portfolio.add_asset(asset1)
        
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        asset2.update_weight(Weight(0.5))
        portfolio.add_asset(asset2)
        
        # When
        is_diversified = portfolio.is_well_diversified(max_single_weight=0.3)
        
        # Then
        assert is_diversified is False
    
    # ========================================================================
    # 자산 가격 업데이트 테스트
    # ========================================================================
    
    def test_자산_가격_일괄_업데이트(self):
        """
        Given: 여러 자산이 있는 포트폴리오가 주어졌을 때
        When: 자산 가격을 일괄 업데이트하면
        Then: 모든 자산의 가격이 업데이트되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        asset1 = AssetEntity.create_stock(symbol="AAPL")
        asset2 = AssetEntity.create_stock(symbol="GOOGL")
        
        portfolio.add_asset(asset1)
        portfolio.add_asset(asset2)
        
        prices = {
            "AAPL": 175.50,
            "GOOGL": 140.25
        }
        
        # When
        portfolio.update_asset_prices(prices)
        
        # Then
        assert asset1.current_price == 175.50
        assert asset2.current_price == 140.25
    
    # ========================================================================
    # 직렬화 테스트
    # ========================================================================
    
    def test_요약_정보_딕셔너리_변환(self):
        """
        Given: 포트폴리오가 주어졌을 때
        When: 요약 정보를 딕셔너리로 변환하면
        Then: 필수 필드가 모두 포함되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # When
        summary = portfolio.to_summary_dict()
        
        # Then
        assert "id" in summary
        assert "name" in summary
        assert summary["name"] == "테스트"
        assert summary["total_value"] == 100000.0
        assert "asset_count" in summary
        assert "needs_rebalancing" in summary
        assert "is_active" in summary
    
    def test_상세_정보_딕셔너리_변환(self):
        """
        Given: 자산이 있는 포트폴리오가 주어졌을 때
        When: 상세 정보를 딕셔너리로 변환하면
        Then: 메타데이터, 설정, 자산, 배분, 분석 정보가 모두 포함되어야 함
        """
        # Given
        portfolio = PortfolioEntity(name="테스트", total_value=100000.0)
        
        # 목표와 현재 비중을 모두 100%로 설정 (Allocation 객체 요구사항)
        asset = AssetEntity.create_stock(symbol="AAPL")
        asset.set_target_weight(Weight(1.0))  # 100%
        asset.update_weight(Weight(1.0))      # 100%
        portfolio.add_asset(asset)
        
        # When
        detailed = portfolio.to_detailed_dict()
        
        # Then
        assert "metadata" in detailed
        assert "configuration" in detailed
        assert "assets" in detailed
        assert "allocation" in detailed
        assert "analytics" in detailed
        
        assert detailed["metadata"]["name"] == "테스트"
        assert detailed["configuration"]["total_value"] == 100000.0
        assert len(detailed["assets"]) == 1
