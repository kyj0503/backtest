"""
현금 자산 처리 테스트
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, patch
from app.services.portfolio_service import PortfolioBacktestService
from app.models.schemas import PortfolioBacktestRequest, PortfolioStock

# 단위 테스트 마커 설정
pytestmark = pytest.mark.unit


class TestCashAssets:
    """현금 자산 처리 관련 테스트"""

    @pytest.mark.asyncio
    async def test_cash_only_portfolio(self):
        """현금만 있는 포트폴리오 테스트"""
        # Given
        request = PortfolioBacktestRequest(
            portfolio=[
                PortfolioStock(
                    symbol="CASH",
                    amount=10000.0,
                    investment_type="lump_sum",
                    dca_periods=12,
                    asset_type="cash"
                )
            ],
            start_date="2023-01-01",
            end_date="2023-12-31",
            commission=0.002,
            rebalance_frequency="monthly",
            strategy="buy_and_hold",
            strategy_params={}
        )
        
        service = PortfolioBacktestService()
        
        # When
        result = await service.run_portfolio_backtest(request)
        
        # Then
        assert result["status"] == "success"
        assert result["data"]["portfolio_statistics"]["Total_Return"] == 0.0
        assert result["data"]["portfolio_statistics"]["Initial_Value"] == 10000.0
        assert result["data"]["portfolio_statistics"]["Final_Value"] == 10000.0
        assert result["data"]["individual_returns"]["CASH"]["return"] == 0.0
        assert result["data"]["individual_returns"]["CASH"]["asset_type"] == "cash"

    @pytest.mark.asyncio 
    async def test_mixed_cash_and_stock_portfolio(self):
        """현금과 주식이 혼합된 포트폴리오 테스트"""
        # Mock yfinance data for AAPL
        mock_df_data = {
            'Open': [150.0, 155.0, 160.0],
            'High': [155.0, 160.0, 165.0], 
            'Low': [149.0, 154.0, 159.0],
            'Close': [154.0, 159.0, 164.0],
            'Volume': [1000000, 1100000, 1200000]
        }
        
        with patch('app.services.yfinance_db.load_ticker_data') as mock_load:
            import pandas as pd
            from datetime import datetime
            
            # Create mock DataFrame with proper index
            dates = pd.date_range('2023-01-02', periods=3)
            mock_df = pd.DataFrame(mock_df_data, index=dates)
            mock_load.return_value = mock_df
            
            # Given
            request = PortfolioBacktestRequest(
                portfolio=[
                    PortfolioStock(
                        symbol="CASH",
                        amount=5000.0,
                        investment_type="lump_sum", 
                        dca_periods=12,
                        asset_type="cash"
                    ),
                    PortfolioStock(
                        symbol="AAPL",
                        amount=5000.0,
                        investment_type="lump_sum",
                        dca_periods=12,
                        asset_type="stock"
                    )
                ],
                start_date="2023-01-01",
                end_date="2023-01-31",
                commission=0.002,
                rebalance_frequency="monthly",
                strategy="buy_and_hold",
                strategy_params={}
            )
            
            service = PortfolioBacktestService()
            
            # When
            result = await service.run_portfolio_backtest(request)
            
            # Then
            assert result["status"] == "success"
            
            # 현금 부분은 수익률 0%
            assert result["data"]["individual_returns"]["CASH"]["return"] == 0.0
            assert result["data"]["individual_returns"]["CASH"]["asset_type"] == "cash"
            assert result["data"]["individual_returns"]["CASH"]["amount"] == 5000.0
            
            # AAPL 부분은 실제 수익률 계산됨
            aapl_return = result["data"]["individual_returns"]["AAPL_1"]["return"]
            assert aapl_return != 0.0  # 수익률이 계산되어야 함
            
            # 포트폴리오 전체 수익률은 가중 평균
            portfolio_return = result["data"]["portfolio_statistics"]["Total_Return"]
            expected_return = (0.0 * 0.5) + (aapl_return * 0.5)  # 50:50 비중
            assert abs(portfolio_return - expected_return) < 0.01

    @pytest.mark.asyncio
    async def test_multiple_cash_entries(self):
        """여러 현금 항목이 있는 포트폴리오 테스트 (현금 합산)"""
        # Given
        request = PortfolioBacktestRequest(
            portfolio=[
                PortfolioStock(
                    symbol="CASH",
                    amount=3000.0,
                    investment_type="lump_sum",
                    dca_periods=12,
                    asset_type="cash"
                ),
                PortfolioStock(
                    symbol="CASH", 
                    amount=7000.0,
                    investment_type="lump_sum",
                    dca_periods=12,
                    asset_type="cash"
                )
            ],
            start_date="2023-01-01",
            end_date="2023-12-31", 
            commission=0.002,
            rebalance_frequency="monthly",
            strategy="buy_and_hold",
            strategy_params={}
        )
        
        service = PortfolioBacktestService()
        
        # When
        result = await service.run_portfolio_backtest(request)
        
        # Then
        assert result["status"] == "success"
        assert result["data"]["portfolio_statistics"]["Total_Return"] == 0.0
        assert result["data"]["portfolio_statistics"]["Final_Value"] == 10000.0  # 3000 + 7000
        assert result["data"]["individual_returns"]["CASH"]["return"] == 0.0

    @pytest.mark.asyncio
    async def test_cash_dca_investment(self):
        """현금 자산의 DCA 투자 방식 테스트 (수익률은 여전히 0%이어야 함)"""
        # Given
        request = PortfolioBacktestRequest(
            portfolio=[
                PortfolioStock(
                    symbol="CASH",
                    amount=12000.0,
                    investment_type="dca",
                    dca_periods=12,
                    asset_type="cash"
                )
            ],
            start_date="2023-01-01",
            end_date="2023-12-31",
            commission=0.002,
            rebalance_frequency="monthly",
            strategy="buy_and_hold",
            strategy_params={}
        )
        
        service = PortfolioBacktestService()
        
        # When
        result = await service.run_portfolio_backtest(request)
        
        # Then
        assert result["status"] == "success"
        assert result["data"]["portfolio_statistics"]["Total_Return"] == 0.0
        assert result["data"]["portfolio_statistics"]["Final_Value"] == 12000.0
        assert result["data"]["individual_returns"]["CASH"]["return"] == 0.0
