import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.core.exceptions import BacktestError
from app.models.schemas import StockPrice

class StockService:
    """주식 데이터 서비스 클래스"""
    
    @staticmethod
    def get_recent_prices(symbol: str, days: int = 5) -> Dict:
        """
        최근 N일간의 주가 데이터를 조회합니다.
        
        Parameters
        ----------
        symbol : str
            주식 심볼 (예: "AAPL")
        days : int, optional
            조회할 일수 (기본값: 5)
            
        Returns
        -------
        Dict
            주가 데이터와 메타데이터를 포함한 딕셔너리
        """
        try:
            # 티커 객체 생성
            ticker = yf.Ticker(symbol)
            
            # 최근 데이터 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 1)  # 여유있게 하루 더
            
            hist = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval="1d"
            )
            
            if hist.empty:
                raise BacktestError(
                    f"'{symbol}' 종목에 대한 데이터가 존재하지 않습니다.",
                    "NO_DATA"
                )
            
            # 데이터 전처리
            hist = hist.tail(days)  # 요청한 일수만큼만 선택
            
            # 응답 데이터 구성
            prices = []
            for date, row in hist.iterrows():
                price_data = StockPrice(
                    date=date.strftime('%Y-%m-%d'),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume'])
                )
                prices.append(price_data)
            
            return {
                'symbol': symbol.upper(),
                'last_updated': datetime.now(),
                'prices': prices
            }
            
        except Exception as e:
            if "Symbol may be delisted" in str(e):
                raise BacktestError(
                    f"'{symbol}' 종목이 상장폐지되었거나 존재하지 않습니다.",
                    "INVALID_SYMBOL"
                )
            raise BacktestError(
                f"주가 데이터 조회 중 오류 발생: {str(e)}",
                "DATA_FETCH_ERROR"
            ) 