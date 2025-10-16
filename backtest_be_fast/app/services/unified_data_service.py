"""
데이터 수집 서비스

**역할**:
- 백테스트 실행 후 프론트엔드가 필요로 하는 모든 추가 데이터를 한 번에 수집
- 여러 데이터 소스로부터 데이터를 병렬로 가져와 응답 시간 최적화

**수집 데이터 목록**:
1. stock_data: 개별 종목의 주가 데이터 (OHLCV)
2. exchange_rate: USD/KRW 환율 데이터 및 통계 (시작/종료/최고/최저)
3. surge_plunge: 급등/급락 이벤트 (5% 이상 변동)
4. benchmarks: 벤치마크 지수 (S&P 500, NASDAQ)
5. news: 종목 관련 최신 뉴스 (네이버 검색 API)

**주요 기능**:
- collect_all_data(): 모든 데이터를 병렬로 수집하여 딕셔너리로 반환
- 에러 발생 시 빈 데이터 반환으로 백테스트 결과는 보존

**의존성**:
- app/services/data_service.py: 주가 데이터 조회
- app/services/news_service.py: 뉴스 데이터 조회
- app/utils/data_fetcher.py: 환율/벤치마크 데이터 페칭

**연관 컴포넌트**:
- Backend: app/api/v1/endpoints/backtest.py (데이터 수집 호출)
- Frontend: src/features/backtest/components/ResultDisplay.tsx (데이터 표시)
- Frontend: src/features/backtest/hooks/useBacktestResult.ts (데이터 처리)

**최적화**:
- 병렬 요청으로 전체 응답 시간 단축
- 개별 데이터 소스 실패 시에도 나머지 데이터 반환
"""
import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime

from .data_service import data_service
from ..core.config import settings

logger = logging.getLogger(__name__)


class UnifiedDataService:
    """통합 데이터 수집 서비스"""
    
    def __init__(self, news_service=None):
        """
        Args:
            news_service: 뉴스 서비스 인스턴스 (의존성 주입)
        """
        self.news_service = news_service
    
    def collect_stock_data(
        self, 
        symbols: List[str], 
        start_date: str, 
        end_date: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        주가 데이터 수집
        
        Args:
            symbols: 종목 심볼 리스트
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            종목별 주가 데이터 딕셔너리
        """
        stock_data = {}
        for symbol in symbols:
            try:
                df = data_service.get_ticker_data_sync(symbol, start_date, end_date)
                if df is not None and not df.empty:
                    stock_data[symbol] = self._transform_stock_data(df)
                else:
                    stock_data[symbol] = []
            except Exception as e:
                logger.warning(f"주가 데이터 수집 실패: {symbol} - {str(e)}")
                stock_data[symbol] = []
        
        return stock_data
    
    def collect_exchange_data(
        self, 
        start_date: str, 
        end_date: str
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        환율 데이터 및 통계 수집
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            (환율 데이터 리스트, 환율 통계 딕셔너리) 튜플
        """
        exchange_rates = []
        exchange_stats = {}
        
        try:
            exchange_data = data_service.get_ticker_data_sync(
                settings.exchange_rate_ticker,
                start_date,
                end_date
            )
            
            if exchange_data is not None and not exchange_data.empty:
                exchange_rates = self._transform_exchange_data(exchange_data)
                
                if exchange_rates:
                    exchange_stats = self._calculate_exchange_stats(exchange_rates)
                    
        except Exception as e:
            logger.warning(f"환율 데이터 수집 실패: {str(e)}")
        
        return exchange_rates, exchange_stats
    
    def collect_volatility_events(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        threshold: float = 5.0,
        max_events_per_symbol: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        급등/급락 이벤트 수집
        
        Args:
            symbols: 종목 심볼 리스트
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            threshold: 급등/급락 기준 (%) - 기본값 5%
            max_events_per_symbol: 종목당 최대 이벤트 수
            
        Returns:
            종목별 급등/급락 이벤트 딕셔너리
        """
        volatility_events = {}
        
        for symbol in symbols:
            try:
                df = data_service.get_ticker_data_sync(symbol, start_date, end_date)
                if df is not None and not df.empty:
                    events = self._calculate_volatility_events(
                        df, 
                        threshold, 
                        max_events_per_symbol
                    )
                    volatility_events[symbol] = events
                else:
                    volatility_events[symbol] = []
            except Exception as e:
                logger.warning(f"급등락 이벤트 수집 실패: {symbol} - {str(e)}")
                volatility_events[symbol] = []
        
        return volatility_events
    
    def collect_benchmark_data(
        self,
        start_date: str,
        end_date: str
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        벤치마크 데이터 수집 (S&P 500, NASDAQ)
        
        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            
        Returns:
            (S&P 500 데이터, NASDAQ 데이터) 튜플
        """
        sp500_benchmark = self._collect_single_benchmark('^GSPC', start_date, end_date)
        nasdaq_benchmark = self._collect_single_benchmark('^IXIC', start_date, end_date)
        
        return sp500_benchmark, nasdaq_benchmark
    
    def collect_latest_news(
        self,
        symbols: List[str],
        display: int = 15
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        최신 뉴스 수집
        
        Args:
            symbols: 종목 심볼 리스트
            display: 종목당 뉴스 개수
            
        Returns:
            종목별 뉴스 딕셔너리
        """
        if not self.news_service:
            logger.warning("뉴스 서비스가 초기화되지 않았습니다.")
            return {symbol: [] for symbol in symbols}
        
        latest_news = {}
        for symbol in symbols:
            try:
                search_query = self.news_service.TICKER_MAPPING.get(symbol, symbol)
                news_list = self.news_service.search_news(search_query, display=display)
                latest_news[symbol] = news_list
                logger.info(f"{symbol} 뉴스 {len(news_list)}개 수집 완료")
            except Exception as e:
                logger.warning(f"{symbol} 뉴스 수집 실패: {str(e)}")
                latest_news[symbol] = []
        
        return latest_news
    
    def collect_all_unified_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        include_news: bool = True,
        news_display_count: int = 15
    ) -> Dict[str, Any]:
        """
        모든 통합 데이터를 한 번에 수집
        
        Args:
            symbols: 종목 심볼 리스트
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            include_news: 뉴스 포함 여부
            news_display_count: 종목당 뉴스 개수
            
        Returns:
            모든 통합 데이터를 포함하는 딕셔너리
        """
        # 주가 데이터
        stock_data = self.collect_stock_data(symbols, start_date, end_date)
        
        # 환율 데이터 및 통계
        exchange_rates, exchange_stats = self.collect_exchange_data(start_date, end_date)
        
        # 급등/급락 이벤트
        volatility_events = self.collect_volatility_events(symbols, start_date, end_date)
        
        # 벤치마크 데이터
        sp500_benchmark, nasdaq_benchmark = self.collect_benchmark_data(start_date, end_date)
        
        # 뉴스 (선택적)
        latest_news = {}
        if include_news:
            latest_news = self.collect_latest_news(symbols, news_display_count)
        
        logger.info(
            f"통합 데이터 수집 완료: "
            f"{len(symbols)}개 종목, "
            f"{len(exchange_rates)}개 환율 데이터, "
            f"{len(latest_news)}개 종목 뉴스"
        )
        
        return {
            'stock_data': stock_data,
            'exchange_rates': exchange_rates,
            'exchange_stats': exchange_stats,
            'volatility_events': volatility_events,
            'sp500_benchmark': sp500_benchmark,
            'nasdaq_benchmark': nasdaq_benchmark,
            'latest_news': latest_news
        }
    
    # ========================================
    # Private Helper Methods
    # ========================================
    
    def _transform_stock_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """주가 DataFrame을 딕셔너리 리스트로 변환"""
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'price': float(row['Close']),
                'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0
            }
            for date, row in df.iterrows()
        ]
    
    def _transform_exchange_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """환율 DataFrame을 딕셔너리 리스트로 변환"""
        return [
            {
                'date': date.strftime('%Y-%m-%d'),
                'rate': float(row['Close'])
            }
            for date, row in df.iterrows()
        ]
    
    def _calculate_exchange_stats(self, exchange_rates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """환율 주요 지점 통계 계산"""
        if not exchange_rates:
            return {}
        
        rates = [item['rate'] for item in exchange_rates]
        min_rate = min(rates)
        max_rate = max(rates)
        start_rate = exchange_rates[0]['rate']
        end_rate = exchange_rates[-1]['rate']
        
        # 최고점과 최저점의 날짜 찾기
        max_rate_date = next(item['date'] for item in exchange_rates if item['rate'] == max_rate)
        min_rate_date = next(item['date'] for item in exchange_rates if item['rate'] == min_rate)
        
        return {
            'start_point': {
                'rate': start_rate,
                'date': exchange_rates[0]['date']
            },
            'end_point': {
                'rate': end_rate,
                'date': exchange_rates[-1]['date']
            },
            'high_point': {
                'rate': max_rate,
                'date': max_rate_date
            },
            'low_point': {
                'rate': min_rate,
                'date': min_rate_date
            }
        }
    
    def _calculate_volatility_events(
        self,
        df: pd.DataFrame,
        threshold: float,
        max_events: int
    ) -> List[Dict[str, Any]]:
        """급등/급락 이벤트 계산"""
        df = df.copy()
        df['daily_return'] = df['Close'].pct_change() * 100
        significant_moves = df[abs(df['daily_return']) >= threshold].copy()
        
        events = []
        for date, row in significant_moves.iterrows():
            events.append({
                'date': date.strftime('%Y-%m-%d'),
                'daily_return': float(row['daily_return']),
                'close_price': float(row['Close']),
                'volume': int(row.get('Volume', 0)) if pd.notna(row.get('Volume', 0)) else 0,
                'event_type': '급등' if row['daily_return'] > 0 else '급락'
            })
        
        # 날짜 역순 정렬 후 상위 N개만 반환
        events.sort(key=lambda x: x['date'], reverse=True)
        return events[:max_events]
    
    def _collect_single_benchmark(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """단일 벤치마크 데이터 수집"""
        try:
            df = data_service.get_ticker_data_sync(ticker, start_date, end_date)
            if df is not None and not df.empty:
                return [
                    {
                        'date': date.strftime('%Y-%m-%d'),
                        'close': float(row['Close'])
                    }
                    for date, row in df.iterrows()
                ]
        except Exception as e:
            logger.warning(f"{ticker} 벤치마크 데이터 수집 실패: {str(e)}")
        
        return []


# 싱글톤 인스턴스 (뉴스 서비스는 나중에 주입)
unified_data_service = UnifiedDataService()
