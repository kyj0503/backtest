"""
테스트용 모의 데이터 생성기

⚠️ 주의: 이 모듈은 yfinance API를 전혀 사용하지 않습니다!
✅ 순수하게 수학적 알고리즘(기하 브라운 운동)으로 가짜 주식 데이터를 생성합니다.
✅ 네트워크 연결이나 외부 API 없이도 테스트가 가능합니다.
✅ 항상 동일한 결과를 보장하여 테스트의 일관성을 유지합니다.
✅ 실제 DB 스키마(stock_data_cache)와 백엔드 데이터 구조에 맞춘 데이터를 생성합니다.
"""
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class MockStockDataGenerator:
    """
    실제 DB 스키마에 맞는 모의 주식 데이터 생성기
    
    데이터베이스 테이블 구조:
    - stocks: 주식 기본 정보 (ticker, name, sector, etc.)
    - daily_prices: 일별 OHLCV 데이터 
    - dividends: 배당 정보
    - stock_splits: 주식 분할 정보
    """
    
    def __init__(self):
        """고정된 시드로 재현 가능한 결과 보장"""
        np.random.seed(42)  # 테스트 일관성을 위한 고정 시드
        
        # 메타데이터 로드
        self.stock_metadata = self._load_stock_metadata()
    
    def _load_stock_metadata(self) -> Dict:
        """주식 메타데이터 로드"""
        try:
            metadata_path = Path(__file__).parent / "stock_metadata.json"
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # 기본 메타데이터 반환
            return {
                "AAPL": {
                    "name": "Apple Inc.",
                    "sector": "Technology",
                    "base_price": 150.0,
                    "volatility": 0.025,
                    "trend": 0.0002,
                    "typical_volume": 50000000
                }
            }
    
    def create_daily_prices_data(
        self,
        ticker: str = "AAPL",
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2024, 1, 1),
        scenario: str = "normal"
    ) -> pd.DataFrame:
        """
        daily_prices 테이블 구조에 맞는 OHLCV 데이터 생성
        
        Args:
            ticker: 주식 티커
            start_date: 시작 날짜
            end_date: 종료 날짜
            scenario: 시나리오 ('normal', 'empty', 'insufficient', 'volatile')
            
        Returns:
            DataFrame with columns: ['Open', 'High', 'Low', 'Close', 'Volume']
            - DB 스키마: open, high, low, close, adj_close, volume
            - 백엔드 요구사항: 'Open', 'High', 'Low', 'Close', 'Volume' 컬럼명
        """
        
        if scenario == "empty":
            return pd.DataFrame()
        
        if scenario == "insufficient":
            # 1개 행만 반환 (데이터 부족 시나리오)
            return pd.DataFrame({
                'Open': [100.0],
                'High': [105.0], 
                'Low': [95.0],
                'Close': [102.0],
                'Volume': [1000000]
            }, index=[start_date])
        
        # 메타데이터에서 주식 정보 가져오기
        stock_info = self.stock_metadata.get(ticker, self.stock_metadata["AAPL"])
        
        if stock_info["base_price"] is None:  # INVALID 티커 처리
            return pd.DataFrame()
        
        # 날짜 범위 생성 (주말 제외 - 주식 시장 특성 반영)
        dates = pd.bdate_range(start=start_date, end=end_date)
        
        if len(dates) == 0:
            return pd.DataFrame()
        
        # 시나리오별 변동성 조정
        volatility = stock_info["volatility"]
        if scenario == "volatile":
            volatility *= 2.0
        
        # 기하 브라운 운동으로 주가 시뮬레이션 (실제 주식 모델링)
        returns = np.random.normal(
            stock_info["trend"], 
            volatility, 
            len(dates)
        )
        price_series = stock_info["base_price"] * np.exp(np.cumsum(returns))
        
        # OHLCV 데이터 생성
        data = []
        prev_close = stock_info["base_price"]
        
        for i, (date_val, close_price) in enumerate(zip(dates, price_series)):
            # 일일 변동 생성
            daily_vol = volatility * 0.5
            
            # Open: 전날 Close에서 갭 반영
            gap = np.random.normal(0, volatility * 0.2)
            open_price = prev_close * (1 + gap)
            
            # High/Low: Close 기준으로 변동
            high_mult = 1 + abs(np.random.normal(0, daily_vol))
            low_mult = 1 - abs(np.random.normal(0, daily_vol))
            
            high = max(open_price, close_price) * high_mult
            low = min(open_price, close_price) * low_mult
            
            # High/Low 범위 내에서 Open/Close 조정
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # 거래량: 로그 정규 분포 (실제 거래량 분포와 유사)
            volume_base = np.log(stock_info["typical_volume"])
            volume = int(np.random.lognormal(volume_base, 0.3))
            
            data.append({
                'Open': round(open_price, 4),      # DB: DECIMAL(19, 4)
                'High': round(high, 4),
                'Low': round(low, 4), 
                'Close': round(close_price, 4),
                'Volume': volume                   # DB: BIGINT UNSIGNED
            })
            
            prev_close = close_price
        
        df = pd.DataFrame(data, index=dates)
        return df
    
    def create_multiindex_data(self, ticker: str = "AAPL") -> pd.DataFrame:
        """
        yfinance 스타일 MultiIndex 컬럼 데이터 생성
        백엔드에서 처리하는 MultiIndex 케이스 테스트용
        """
        # 기본 데이터 생성
        data = self.create_daily_prices_data(
            ticker=ticker,
            start_date=date(2023, 1, 1), 
            end_date=date(2023, 1, 10)
        )
        
        if data.empty:
            return data
        
        # MultiIndex 컬럼 생성 (yfinance 패턴)
        columns = pd.MultiIndex.from_product(
            [['Open', 'High', 'Low', 'Close', 'Volume'], [ticker]],
            names=['Price', 'Ticker']
        )
        
        # 데이터를 MultiIndex 형태로 변환
        multi_data = data.copy()
        multi_data.columns = columns
        
        return multi_data
    
    def create_stock_info(self, ticker: str) -> Dict:
        """
        stocks 테이블의 info_json 컬럼에 저장될 정보 생성
        yfinance의 .info 응답과 유사한 구조
        """
        stock_meta = self.stock_metadata.get(ticker, {})
        
        if not stock_meta or stock_meta.get("name") is None:
            return {}  # INVALID 티커
        
        return {
            "symbol": ticker,
            "longName": stock_meta["name"],
            "sector": stock_meta["sector"],
            "currency": "USD",
            "exchange": "NMS",
            "marketCap": int(stock_meta["base_price"] * 1000000000),
            "sharesOutstanding": 1000000000,
            "beta": round(np.random.uniform(0.8, 1.2), 2),
            "trailingPE": round(np.random.uniform(15, 30), 2),
            "dividendYield": round(np.random.uniform(0.01, 0.03), 4)
        }


# 전역 인스턴스 생성
_mock_generator = MockStockDataGenerator()


# 테스트에서 사용할 미리 정의된 데이터셋
MOCK_DATASETS = {
    'AAPL_NORMAL': _mock_generator.create_daily_prices_data('AAPL'),
    'GOOGL_NORMAL': _mock_generator.create_daily_prices_data('GOOGL'),
    'MSFT_NORMAL': _mock_generator.create_daily_prices_data('MSFT'),
    'TSLA_NORMAL': _mock_generator.create_daily_prices_data('TSLA'),
    'EMPTY': _mock_generator.create_daily_prices_data('INVALID', scenario='empty'),
    'INSUFFICIENT': _mock_generator.create_daily_prices_data('AAPL', scenario='insufficient'),
    'MULTIINDEX': _mock_generator.create_multiindex_data('AAPL')
}


# 편의 함수들
def get_mock_stock_data(ticker: str, scenario: str = "normal") -> pd.DataFrame:
    """모의 주식 데이터 생성 편의 함수"""
    return _mock_generator.create_daily_prices_data(ticker=ticker, scenario=scenario)


def get_mock_stock_info(ticker: str) -> Dict:
    """모의 주식 정보 생성 편의 함수"""
    return _mock_generator.create_stock_info(ticker)


# yfinance 모킹용 클래스
class MockYFinanceTicker:
    """yfinance.Ticker 모킹 클래스"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self._info = get_mock_stock_info(ticker)
    
    def history(self, start=None, end=None, **kwargs) -> pd.DataFrame:
        """history 메서드 모킹"""
        if not self._info:  # INVALID 티커
            return pd.DataFrame()
        
        start_date = pd.to_datetime(start).date() if start else date(2023, 1, 1)
        end_date = pd.to_datetime(end).date() if end else date(2024, 1, 1)
        
        return get_mock_stock_data(self.ticker)
    
    @property
    def info(self) -> Dict:
        """info 프로퍼티 모킹"""
        return self._info


def mock_yf_download(ticker, start=None, end=None, **kwargs) -> pd.DataFrame:
    """yfinance.download 함수 모킹"""
    if isinstance(ticker, list):
        ticker = ticker[0]  # 첫 번째 티커만 사용
    
    return get_mock_stock_data(ticker)
