"""
완전 오프라인 Mock 주식 데이터 생성기
Geometric Brownian Motion 알고리즘으로 현실적 주식 데이터 생성
DB 스키마 (DECIMAL 19,4) 완전 호환
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
import random


class MockStockDataGenerator:
    """
    수학적 모델링 기반 주식 데이터 생성기
    - Geometric Brownian Motion으로 현실적 가격 변동
    - OHLCV 데이터 논리적 일관성 보장
    - DB 스키마 (DECIMAL 19,4) 정밀도 준수
    """
    
    def __init__(self, seed: int = 42):
        """
        Args:
            seed: 재현 가능한 결과를 위한 시드값
        """
        np.random.seed(seed)
        random.seed(seed)
        
        # 주식별 기본 파라미터
        self.stock_params = {
            'AAPL': {
                'initial_price': 150.0,
                'volatility': 0.25,
                'drift': 0.08,
                'avg_volume': 50000000
            },
            'GOOGL': {
                'initial_price': 2800.0,
                'volatility': 0.22,
                'drift': 0.06,
                'avg_volume': 1500000
            },
            'MSFT': {
                'initial_price': 300.0,
                'volatility': 0.20,
                'drift': 0.10,
                'avg_volume': 30000000
            },
            'TSLA': {
                'initial_price': 800.0,
                'volatility': 0.45,
                'drift': 0.15,
                'avg_volume': 25000000
            },
            'DEFAULT': {
                'initial_price': 100.0,
                'volatility': 0.25,
                'drift': 0.05,
                'avg_volume': 10000000
            }
        }
    
    def _to_decimal(self, value: float, precision: int = 4) -> Decimal:
        """
        MySQL DECIMAL(19,4) 형식으로 변환
        """
        return Decimal(str(round(value, precision))).quantize(
            Decimal('0.0001'), rounding=ROUND_HALF_UP
        )
    
    def generate_ohlcv_data(
        self, 
        ticker: str,
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2023, 12, 31),
        scenario: str = 'normal'
    ) -> pd.DataFrame:
        """
        OHLCV 데이터 생성
        
        Args:
            ticker: 종목 심볼
            start_date: 시작 날짜
            end_date: 종료 날짜
            scenario: 시나리오 ('normal', 'volatile', 'trending', 'crash')
        
        Returns:
            OHLCV 데이터가 담긴 DataFrame
        """
        if scenario == 'empty':
            # 빈 데이터 시나리오
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        # 종목별 파라미터 가져오기
        params = self.stock_params.get(ticker, self.stock_params['DEFAULT'])
        
        # 시나리오별 파라미터 조정
        if scenario == 'volatile':
            params = params.copy()
            params['volatility'] *= 2.0
        elif scenario == 'trending':
            params = params.copy()
            params['drift'] *= 1.5
        elif scenario == 'crash':
            params = params.copy()
            params['drift'] = -0.3
            params['volatility'] *= 1.5
        
        # 날짜 범위 생성 (주말 제외)
        date_range = pd.bdate_range(start_date, end_date)
        n_days = len(date_range)
        
        if n_days == 0:
            return pd.DataFrame(columns=['Open', 'High', 'Low', 'Close', 'Volume'])
        
        # Geometric Brownian Motion으로 종가 생성
        dt = 1/252  # 1 trading day
        drift = params['drift']
        volatility = params['volatility']
        
        # 가격 경로 생성
        returns = np.random.normal(
            (drift - 0.5 * volatility**2) * dt,
            volatility * np.sqrt(dt),
            n_days
        )
        
        price_path = [params['initial_price']]
        for i in range(n_days):
            price_path.append(price_path[-1] * np.exp(returns[i]))
        
        # OHLC 생성 (Close 기준)
        closes = np.array(price_path[1:])
        
        # Open은 이전 날 Close에 갭 적용
        gap_factors = np.random.normal(1.0, 0.005, n_days)  # 0.5% 갭
        opens = np.concatenate([[params['initial_price']], closes[:-1]]) * gap_factors
        
        # High/Low는 Open/Close 기준으로 생성
        daily_ranges = np.random.uniform(0.01, 0.05, n_days)  # 1-5% 일일 변동폭
        
        highs = []
        lows = []
        
        for i in range(n_days):
            open_price = opens[i]
            close_price = closes[i]
            daily_range = daily_ranges[i]
            
            # High는 Open/Close 중 높은 값 이상
            base_high = max(open_price, close_price)
            high = base_high * (1 + np.random.uniform(0, daily_range))
            
            # Low는 Open/Close 중 낮은 값 이하
            base_low = min(open_price, close_price)
            low = base_low * (1 - np.random.uniform(0, daily_range))
            
            highs.append(high)
            lows.append(low)
        
        highs = np.array(highs)
        lows = np.array(lows)
        
        # Volume 생성 (가격 변동성과 연관)
        price_changes = np.abs(np.diff(closes, prepend=opens[0]))
        volume_multipliers = 1 + price_changes / closes
        volumes = params['avg_volume'] * volume_multipliers * np.random.uniform(0.5, 2.0, n_days)
        volumes = volumes.astype(int)
        
        # DataFrame 생성 (DECIMAL 정밀도 적용)
        df = pd.DataFrame({
            'Open': [float(self._to_decimal(price)) for price in opens],
            'High': [float(self._to_decimal(price)) for price in highs],
            'Low': [float(self._to_decimal(price)) for price in lows],
            'Close': [float(self._to_decimal(price)) for price in closes],
            'Volume': volumes
        }, index=date_range)
        
        # 논리적 일관성 검증 및 수정
        for i in range(len(df)):
            row = df.iloc[i]
            open_val, high_val, low_val, close_val = row['Open'], row['High'], row['Low'], row['Close']
            
            # High는 Open/Close보다 높거나 같아야 함
            df.iloc[i, df.columns.get_loc('High')] = max(high_val, open_val, close_val)
            
            # Low는 Open/Close보다 낮거나 같아야 함
            df.iloc[i, df.columns.get_loc('Low')] = min(low_val, open_val, close_val)
        
        return df
    
    def generate_ticker_info(self, ticker: str) -> Dict:
        """
        종목 정보 생성
        """
        info_templates = {
            'AAPL': {
                'company_name': 'Apple Inc.',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'country': 'United States',
                'currency': 'USD',
                'market_cap': 3000000000000,
                'employees': 164000
            },
            'GOOGL': {
                'company_name': 'Alphabet Inc.',
                'sector': 'Communication Services',
                'industry': 'Internet Content & Information',
                'country': 'United States',
                'currency': 'USD',
                'market_cap': 1800000000000,
                'employees': 156500
            },
            'MSFT': {
                'company_name': 'Microsoft Corporation',
                'sector': 'Technology',
                'industry': 'Software—Infrastructure',
                'country': 'United States',
                'currency': 'USD',
                'market_cap': 2500000000000,
                'employees': 221000
            },
            'DEFAULT': {
                'company_name': f'{ticker} Corporation',
                'sector': 'Technology',
                'industry': 'Software',
                'country': 'United States',
                'currency': 'USD',
                'market_cap': 50000000000,
                'employees': 10000
            }
        }
        
        return info_templates.get(ticker, info_templates['DEFAULT'])
    
    def generate_multiple_stocks_data(
        self,
        tickers: List[str],
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2023, 12, 31)
    ) -> Dict[str, pd.DataFrame]:
        """
        여러 종목의 데이터 동시 생성
        """
        return {
            ticker: self.generate_ohlcv_data(ticker, start_date, end_date)
            for ticker in tickers
        }
    
    def get_test_scenarios(self) -> Dict[str, Dict]:
        """
        테스트 시나리오 정의
        """
        return {
            'normal': {
                'description': '정상적인 시장 상황',
                'tickers': ['AAPL', 'GOOGL'],
                'expected_data_points': 252,  # 1년 영업일
                'expected_volatility_range': (0.15, 0.35)
            },
            'volatile': {
                'description': '높은 변동성 시장',
                'tickers': ['TSLA'],
                'expected_data_points': 126,  # 6개월 영업일
                'expected_volatility_range': (0.40, 0.60)
            },
            'empty': {
                'description': '데이터 없음 시나리오',
                'tickers': ['INVALID'],
                'expected_data_points': 0,
                'expected_volatility_range': None
            },
            'crash': {
                'description': '시장 급락 시나리오',
                'tickers': ['AAPL'],
                'expected_data_points': 60,  # 3개월 영업일
                'expected_volatility_range': (0.30, 0.70)
            }
        }
