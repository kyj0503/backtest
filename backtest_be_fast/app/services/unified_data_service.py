"""통합 데이터 수집 서비스

주가, 환율, 벤치마크, 뉴스 등 백테스트 관련 데이터를 한 번에 수집합니다.
병렬 요청으로 응답 시간을 최적화하고, 개별 실패 시에도 나머지 데이터를 반환합니다.
"""
import asyncio
import concurrent.futures
import logging
import pandas as pd
from typing import List, Dict, Any, Optional

from .data_service import data_service
from app.repositories.stock_repository import get_stock_repository
from ..core.config import settings

logger = logging.getLogger(__name__)


class UnifiedDataService:
    """통합 데이터 수집 서비스"""

    # collect_all_unified_data()의 독립적인 I/O(심볼별 주가, 종목 메타데이터,
    # 환율, 벤치마크, 뉴스)를 병렬 실행할 때 사용하는 워커 수 상한. 무제한
    # fan-out은 외부 API(yfinance/Naver) 레이트리밋을 유발할 수 있으므로
    # 작은 값으로 고정한다 (P2-12). DB 커넥션 풀(pool_size=40+overflow=80)
    # 대비로도 충분히 작다.
    _MAX_PARALLEL_WORKERS = 5

    def __init__(self, news_service=None):
        """
        Args:
            news_service: 뉴스 서비스 인스턴스 (의존성 주입)
        """
        self.news_service = news_service
        self.stock_repo = get_stock_repository()
    
    def collect_ticker_info(
        self,
        symbols: List[str]
    ) -> Dict[str, Dict[str, str]]:
        """
        종목별 메타데이터 수집 (currency 포함)

        Args:
            symbols: 종목 심볼 리스트

        Returns:
            종목별 메타데이터 딕셔너리 (currency, company_name, exchange)
        """
        # 배치 조회로 N+1 쿼리 문제 해결
        try:
            ticker_info = self.stock_repo.get_tickers_info_batch(symbols)
        except Exception as e:
            logger.warning(f"티커 정보 일괄 조회 실패: {str(e)}")
            # 실패 시 기본값 반환
            ticker_info = {
                symbol: {
                    'symbol': symbol,
                    'currency': 'USD',
                    'company_name': symbol,
                    'exchange': 'Unknown'
                }
                for symbol in symbols
            }

        return ticker_info

    def collect_stock_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        price_histories: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        주가 데이터 수집

        Args:
            symbols: 종목 심볼 리스트
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            price_histories: 미리 조회된 종목별 주가 히스토리 (선택, P2-12).
                collect_all_unified_data처럼 collect_volatility_events와 데이터를
                공유해 심볼당 중복 조회를 피하고 싶을 때 전달한다. None이면
                이 메서드가 직접 조회한다 (단독 호출 시 기존과 동일하게 동작).

        Returns:
            종목별 주가 데이터 딕셔너리
        """
        stock_data = {}
        for symbol in symbols:
            try:
                if price_histories is not None:
                    df = price_histories.get(symbol)
                else:
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
        threshold: float = None,
        max_events_per_symbol: int = 10,
        price_histories: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        급등/급락 이벤트 수집

        Args:
            symbols: 종목 심볼 리스트
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            threshold: 급등/급락 기준 (%) - 기본값은 settings.volatility_threshold_pct
            max_events_per_symbol: 종목당 최대 이벤트 수
            price_histories: 미리 조회된 종목별 주가 히스토리 (선택, P2-12).
                collect_all_unified_data처럼 collect_stock_data와 데이터를 공유해
                심볼당 중복 조회를 피하고 싶을 때 전달한다. None이면 이 메서드가
                직접 조회한다 (단독 호출 시 기존과 동일하게 동작).

        Returns:
            종목별 급등/급락 이벤트 딕셔너리
        """
        # threshold가 None이면 설정값 사용
        if threshold is None:
            threshold = settings.volatility_threshold_pct

        volatility_events = {}

        for symbol in symbols:
            try:
                if price_histories is not None:
                    df = price_histories.get(symbol)
                else:
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
        end_date: str,
        fill_missing_dates: bool = True
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        벤치마크 데이터 수집 (S&P 500, NASDAQ)

        Args:
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            fill_missing_dates: 누락된 날짜를 forward-fill로 채울지 여부 (기본: True)

        Returns:
            (S&P 500 데이터, NASDAQ 데이터) 튜플
            
        Note:
            fill_missing_dates=True일 경우, 벤치마크 시장 휴장일을 이전 거래일 가격으로 채웁니다.
            이를 통해 다른 시장(예: 한국) 종목과 날짜를 일치시켜 그래프 끊김 현상을 방지합니다.
        """
        sp500_benchmark = self._collect_single_benchmark('^GSPC', start_date, end_date, fill_missing_dates)
        nasdaq_benchmark = self._collect_single_benchmark('^IXIC', start_date, end_date, fill_missing_dates)

        return sp500_benchmark, nasdaq_benchmark

    def calculate_benchmark_return(
        self,
        benchmark_data: List[Dict[str, Any]]
    ) -> float:
        """
        벤치마크 수익률 계산

        Args:
            benchmark_data: 벤치마크 가격 데이터 리스트

        Returns:
            총 수익률 (%)
        """
        if not benchmark_data or len(benchmark_data) < 2:
            return 0.0

        try:
            # 소스에서 이미 정규화되어 'close' 키만 사용
            first_close = benchmark_data[0]['close']
            last_close = benchmark_data[-1]['close']

            if first_close <= 0:
                return 0.0

            return ((last_close - first_close) / first_close) * 100
        except (KeyError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"벤치마크 수익률 계산 실패: {str(e)}")
            return 0.0
    
    def collect_latest_news(
        self,
        symbols: List[str],
        display: int = 20,
        max_cache_hours: int = 3
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        최신 뉴스 수집 (DB 캐시 우선, 3시간 이상 오래되면 API 호출)

        Args:
            symbols: 종목 심볼 리스트
            display: 종목당 뉴스 개수
            max_cache_hours: 캐시 최대 유효 시간 (기본 3시간)

        Returns:
            종목별 뉴스 딕셔너리
        """
        if not self.news_service:
            logger.warning("뉴스 서비스가 초기화되지 않았습니다.")
            return {symbol: [] for symbol in symbols}

        latest_news = {}
        for symbol in symbols:
            try:
                # 1. DB에서 먼저 조회 (3시간 이내)
                cached_news = self.stock_repo.load_ticker_news(symbol, max_age_hours=max_cache_hours)

                if cached_news and len(cached_news) > 0:
                    # DB에 신선한 데이터가 있으면 반환
                    latest_news[symbol] = cached_news[:display]  # display 개수만큼
                    logger.info(f"{symbol} 뉴스 {len(latest_news[symbol])}개 (DB 캐시 사용)")
                else:
                    # 2. 캐시가 없거나 오래되었으면 API 호출
                    logger.info(f"{symbol} 뉴스 캐시가 없거나 오래됨 - API 호출")
                    search_query = self.news_service.get_ticker_query(symbol)
                    news_list = self.news_service.search_news(search_query, display=display)

                    # 3. API 결과를 DB에 저장
                    if news_list:
                        self.stock_repo.save_ticker_news(symbol, news_list)

                    latest_news[symbol] = news_list
                    logger.info(f"{symbol} 뉴스 {len(news_list)}개 (API 수집 완료)")

            except Exception as e:
                logger.warning(f"{symbol} 뉴스 수집 실패: {str(e)}")
                latest_news[symbol] = []

        return latest_news

    def _fetch_price_history(
        self,
        symbol: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """단일 종목의 주가 히스토리를 조회합니다 (실패 시 빈 DataFrame, P2-12)."""
        try:
            df = data_service.get_ticker_data_sync(symbol, start_date, end_date)
            return df if df is not None else pd.DataFrame()
        except Exception as e:
            logger.warning(f"주가 히스토리 조회 실패: {symbol} - {str(e)}")
            return pd.DataFrame()

    def _fetch_price_histories(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        종목별 주가 히스토리를 병렬로, 심볼당 1회만 조회합니다 (P2-12).

        collect_stock_data와 collect_volatility_events가 결과를 공유하도록 해
        기존에 심볼당 두 번(주가 데이터용, 급등락 이벤트용) 조회하던 중복을
        제거한다. 조회 자체도 bounded ThreadPoolExecutor로 병렬 실행해 종목
        수에 비례해 늘어나던 순차 대기 시간을 없앤다. 워커 수는
        _MAX_PARALLEL_WORKERS로 제한해 외부 API(yfinance) 레이트리밋을 존중한다
        (무제한 fan-out 금지).
        """
        if not symbols:
            return {}

        price_histories: Dict[str, pd.DataFrame] = {}
        max_workers = min(len(symbols), self._MAX_PARALLEL_WORKERS)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_symbol = {
                executor.submit(self._fetch_price_history, symbol, start_date, end_date): symbol
                for symbol in symbols
            }
            for future in concurrent.futures.as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                price_histories[symbol] = future.result()

        return price_histories

    def collect_all_unified_data(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        include_news: bool = True,
        news_display_count: int = 20
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

        Note (P2-12):
            서로 독립적인 I/O(심볼별 주가 히스토리, 종목 메타데이터, 환율,
            벤치마크, 뉴스)를 bounded ThreadPoolExecutor로 병렬 실행한다. 이
            메서드는 엔드포인트에서 asyncio.to_thread로 감싸 워커 스레드에서
            동기적으로 호출되므로(app/api/v1/endpoints/backtest.py), 코루틴이
            아니라 스레드 기반 병렬화를 사용한다. 심볼별 주가 히스토리는
            collect_stock_data/collect_volatility_events 양쪽이 공유하도록 한
            번만 조회한다 (기존에는 심볼당 두 번 조회했다).
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self._MAX_PARALLEL_WORKERS) as executor:
            price_histories_future = executor.submit(
                self._fetch_price_histories, symbols, start_date, end_date
            )
            ticker_info_future = executor.submit(self.collect_ticker_info, symbols)
            exchange_future = executor.submit(self.collect_exchange_data, start_date, end_date)
            benchmark_future = executor.submit(self.collect_benchmark_data, start_date, end_date)
            news_future = (
                executor.submit(self.collect_latest_news, symbols, news_display_count)
                if include_news else None
            )

            price_histories = price_histories_future.result()
            ticker_info = ticker_info_future.result()
            exchange_rates, exchange_stats = exchange_future.result()
            sp500_benchmark, nasdaq_benchmark = benchmark_future.result()
            latest_news = news_future.result() if news_future else {}

        # 이미 조회한 주가 히스토리를 공유해 중복 조회 없이 파생 데이터를 계산한다
        stock_data = self.collect_stock_data(
            symbols, start_date, end_date, price_histories=price_histories
        )
        volatility_events = self.collect_volatility_events(
            symbols, start_date, end_date, price_histories=price_histories
        )

        logger.info(
            f"통합 데이터 수집 완료: "
            f"{len(symbols)}개 종목, "
            f"{len(exchange_rates)}개 환율 데이터, "
            f"{len(latest_news)}개 종목 뉴스"
        )

        return {
            'ticker_info': ticker_info,
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
        end_date: str,
        fill_missing_dates: bool = True
    ) -> List[Dict[str, Any]]:
        """
        단일 벤치마크 데이터 수집

        Args:
            ticker: 벤치마크 티커 (^GSPC, ^IXIC 등)
            start_date: 시작 날짜 (YYYY-MM-DD)
            end_date: 종료 날짜 (YYYY-MM-DD)
            fill_missing_dates: 누락된 날짜 채우기 여부

        Returns:
            벤치마크 데이터 리스트 [{'date': 'YYYY-MM-DD', 'close': float, 'return_pct': float}]

        Note:
            모든 키를 소문자로 정규화하여 일관성 유지.
            fill_missing_dates=True일 경우, 전체 날짜 범위에 대해 forward-fill을 적용하여
            다른 시장 종목과 날짜를 일치시킵니다. 이를 통해 벤치마크 그래프 끊김 현상을 방지합니다.
            일일 수익률(return_pct)도 함께 계산하여 반환합니다.
        """
        try:
            df = data_service.get_ticker_data_sync(ticker, start_date, end_date)
            if df is not None and not df.empty:
                # DataFrame 컬럼명을 소문자로 정규화
                df_normalized = df.copy()
                df_normalized.columns = [col.lower() for col in df_normalized.columns]

                if fill_missing_dates:
                    # 전체 날짜 범위 생성 (주말 포함)
                    full_date_range = pd.date_range(start=start_date, end=end_date, freq='D')
                    
                    # reindex로 누락된 날짜 추가 후 forward-fill
                    df_normalized = df_normalized.reindex(full_date_range).ffill()
                    
                    # 시작 부분에 NaN이 있으면 backward-fill
                    df_normalized = df_normalized.bfill()

                # 일일 수익률 계산
                df_normalized['return_pct'] = df_normalized['close'].pct_change() * 100
                # 첫 날은 0으로 설정
                df_normalized['return_pct'] = df_normalized['return_pct'].fillna(0)

                return [
                    {
                        'date': date.strftime('%Y-%m-%d'),
                        'close': float(row['close']),
                        'return_pct': float(row['return_pct'])
                    }
                    for date, row in df_normalized.iterrows()
                    if pd.notna(row['close'])  # NaN 제외
                ]
        except Exception as e:
            logger.warning(f"{ticker} 벤치마크 데이터 수집 실패: {str(e)}")

        return []


# 싱글톤 인스턴스 (뉴스 서비스는 나중에 주입)
unified_data_service = UnifiedDataService()
